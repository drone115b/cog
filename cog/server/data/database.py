#####################################################################
#
# Copyright 2015 SpinVFX 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License. 
# 
#####################################################################

import sqlite3 as dbi
from . import multilock

import datetime # automated database conversion
import os

import gzip
import shutil


#################################################

try: # version proofing
    def B(x):
        return bytes(x, encoding='ascii')
    B('arbitrary string') # should throw exception in python < 3
except:
    def B(x):
        return x

#################################################

Binary = dbi.Binary

#################################################

class myGzipFile(gzip.GzipFile):
    """wrapper for python 2.6 only.  Not needed in >=2.7"""
    # reference: http://mail.python.org/pipermail/tutor/2009-November/072959.html
    def __enter__(self):
        if self.fileobj is None:
            raise ValueError("I/O operation on closed GzipFile object")
        return self

    def __exit__(self, *args):
        self.close()


#################################################

def check_database(filename, schema_list, logger=None):
    "Will check for an existing database on disk, and build it if necessary"
    
    if not os.path.isfile(filename):
        conn = dbi.connect(filename, isolation_level='EXCLUSIVE')
        for cmd in schema_list :
            conn.execute(cmd, [])
        conn.commit()
   

#################################################

_NOLOCK = 0
_READLOCK = 1
_WRITELOCK = 2
_EXCLUSIVELOCK = 3

#################################################

# use a double precision floating point representation for TIMESTAMP, not the default string representation

_doomsday = datetime.datetime(2017,1,1)
def _adapt_timestamp(ts):
    td = ts - _doomsday
    # safe for python 2.6, >2.6 should probably use timedelta.total_seconds() built-in.
    td = float(td.microseconds * (1.0 / (10.0**6)) + (td.seconds + td.days * 24 * 3600)) 
    return td

def _convert_timestamp(r):
    return _doomsday + datetime.timedelta(seconds=float(r))

# Register the adapter
dbi.register_adapter(datetime.datetime, _adapt_timestamp)

# Register the converter
dbi.register_converter("TIMESTAMP", _convert_timestamp)

#################################################

class Database :
    """Abstracts the sql interface"""
    
    def __init__( self, filename, begin_sql, cache_connection=False, lock=None ) :
        # don't accidentally create a file if it doesn't exist
        self._filename = None
        if filename:
            if os.path.isfile(filename):
                self._filename = filename
        self._begin_sql = begin_sql
        self._cache_connection = cache_connection
        self._conn = None
        if lock is None:
            self._multilock = multilock.Multilock()
        else:
            self._multilock = lock
        self._lockstate = _NOLOCK

        return
        
    def __del__( self ) :
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        
        
    def _lock(self, kind, timeout=2.0):
        succeed = True
        if _NOLOCK == self._lockstate :
            if _READLOCK == kind :
                self._multilock.acquire_read()
            elif _WRITELOCK == kind :
                self._multilock.acquire_write()
            elif _EXCLUSIVELOCK == kind :
                succeed = self._multilock.acquire_exclusive(timeout)
                
            if succeed:
                self._lockstate = kind
        return succeed

    def _unlock(self):
        if _NOLOCK != self._lockstate :
            if _READLOCK == self._lockstate :
                self._multilock.release_read()
            elif _WRITELOCK == self._lockstate :
                self._multilock.release_write()
            elif _EXCLUSIVELOCK == self._lockstate :
                self._multilock.release_exclusive()
                
            self._lockstate = _NOLOCK
        
    def clone(self):
        return Database(self._filename, self._begin_sql, self._cache_connection,  self._multilock ) # share the lock
        
    def sql_begin_read(self) :
        "Transaction begin"
        self._lock(_READLOCK)
        if self._conn is None :
            self._conn = dbi.connect(self._filename, detect_types=dbi.PARSE_DECLTYPES|dbi.PARSE_COLNAMES, isolation_level='DEFERRED', timeout=30.0)
            self._conn.execute(self._begin_sql, [])
        return
        
    def sql_begin_write(self) :
        "Transaction begin"
        self._lock(_WRITELOCK)
        if self._conn is None :
            self._conn = dbi.connect(self._filename, detect_types=dbi.PARSE_DECLTYPES|dbi.PARSE_COLNAMES, isolation_level='DEFERRED', timeout=30.0)
            self._conn.execute(self._begin_sql, [])
        return
        
    def sql_begin_exclusive(self, timeout=2.0) :
        "Transaction begin"
        ret = self._lock(_EXCLUSIVELOCK, timeout)
        if ret :
            self._conn = None
            try:
                self._conn = dbi.connect(self._filename, detect_types=dbi.PARSE_DECLTYPES|dbi.PARSE_COLNAMES, isolation_level='EXCLUSIVE', timeout=timeout)
                self._conn.execute(self._begin_sql, [])
            except:
                ret = False
        return ret

    def sql_end(self):
        "Transaction commit"
        if self._conn is not None :
            self._conn.commit()
            if _EXCLUSIVELOCK == self._lockstate :
                self._conn.close()
                self._conn = None
            self._unlock()
        if self._conn is not None and not self._cache_connection :
            self._conn.close()
            self._conn = None
        return

    def sql_selectvalue(self, cmd, args):
        "Select operation, returning the first value of the first row"
        ret = None
        try :
            curs = self._conn.cursor()
            curs.execute( cmd, args )
            row = curs.fetchone()
            if row is not None :
                if len(row) > 0 :
                    ret = row[0]
        except :
            pass
        
        return ret
            
    def sql_selectrow(self, cmd, args) :
        "Select operation, returning the first row"
        ret = None
        try :
            curs = self._conn.cursor()
            curs.execute( cmd, args )
            ret = curs.fetchone()
        except :
            pass
        
        return ret

    def sql_selectall(self, cmd, args, column_names = False, do_sort = False) :
        "Select operation, returning the resulting table"
        ret = None
        try :
            curs = self._conn.cursor()
            curs.execute( cmd, args )
            rows = list(curs.fetchall())
            if do_sort :
                rows = sorted(rows)
            if column_names :
                cols = [x[0] for x in curs.description]
                rows.insert(0, cols)
            ret = rows
        except :
            pass
        return ret

    def sql_insert(self, cmd, args):
        "Inserts a row, returns its rowid"
        rowid = None
        try:
            curs = self._conn.cursor()
            curs.execute(cmd, args)
            rowid = curs.lastrowid
        except:
            pass
        return rowid

    def sql_update(self, cmd, args) :
        "Write operation, does not return anything"
        try :
            self._conn.execute(cmd, args)
            return True
        except :
            return False
            
            
    def sql_updatemany(self, cmd, args):
        "Multiple writes, given a proper array of args"
        try :
            self._conn.executemany( cmd, args )
            return True
        except :
            return False

    def sql_rollback(self):
        if self._conn is not None:
            self._conn.rollback()

#################################################

def backup(database_name, backup_name):
    if os.path.isfile(database_name):
        tmp_name = backup_name + '.in_progress'
        replacing_name = backup_name + '.replaced'
        conn = dbi.connect(database_name)
        # version-proof python 2.6 / 3.2 using the b() function
        sql_lines = (B('%s\n' % x) for x in conn.iterdump()) # generator, does not pull all into RAM
        with myGzipFile(tmp_name, 'wb', 5) as fout:
            fout.writelines(sql_lines)
        if os.path.isfile(backup_name):
            if os.path.isfile(replacing_name):
                os.remove(replacing_name)
            shutil.move(backup_name, replacing_name)
        shutil.move(tmp_name, backup_name)
        if os.path.isfile(replacing_name):
            os.remove(replacing_name)
    return