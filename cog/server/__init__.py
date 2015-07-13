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

import random
import copy
import logging
import socket 
import inspect
import functools
import threading
import datetime
import base64
import subprocess
import os
import time
import traceback
import json
import itertools
import zlib

# -------------------------------------------------------------------

# TODO : version 2.0, find a way of executing multiple sandboxes, for long-lived jobs.

# -------------------------------------------------------------------

try: # version-proof
    import xmlrpclib as xmlrpc_lib
except ImportError :
    import xmlrpc.client as xmlrpc_lib

try:
  import Queue as queue
except ImportError :
   import queue

# -------------------------------------------------------------------    

from .. import auth # cog authentication
from .. import conf 
from .. import uid
from ..pr import session
from .. import ccn
from .. import ccs
from .. import insp 


# -------------------------------------------------------------------

from .data import database
from . import sandbox
from . import sql

# -------------------------------------------------------------------

# things that we probably don't want to expose to configuration:

NONCE_EXPIRY = 60 # seconds
NONCE_CACHE_LIMIT = 4096

SCHEDULE_INTERVAL = 2 # seconds
SCHEDULE_BEGIN = 30

BACKUP_BEGIN = 60 * 5
MAINTENANCE_BEGIN = 60 * 2

# @@ how to purge old submissions from the database?

# -------------------------------------------------------------------    
#    
# Implements a XML-RPC client base class 
# with decorators to autopopulate from the
# definition of the server:
#
# Unfortunately, XMLRPC does not support optional arguments, so this complicates
# our attempts at simplifying the parameters associated with authentication.
#
class ClientBase( object ) :
  
    def __init__( self, confdict, notifier=None ):
        server_list = [x.strip() for x in confdict['COG_SERVERS'].split(',')]
        assert len(server_list) > 0
        self._server_list = server_list
        self._server_bound = len(server_list)
        assert( self._server_bound )
        self._server_num = random.randint( 0, self._server_bound-1) 
        self._notifier = notifier
        self._conf = confdict

    # ===========================================
          
    def _pick_one( self ):
        # round robin across the servers
        ret = self._server_list[ self._server_num ]
        self._server_num += 1
        self._server_num = 0 if self._server_num == self._server_bound else self._server_num
        return ret
    
    # ===========================================
    
    def _get_user( self, user_index, args, kwargs ):
        if len( args ) > user_index :
            if args[ user_index ] :
                return args[ user_index ]
        else:
            if 'user' in kwargs:
                if kwargs['user']:
                    return kwargs['user']

        return auth.get_username()
            
    # ===========================================
    
    def _set_user( self, user_index, user, args, kwargs ):
        newargs = args
        newkw = kwargs
        if len( args ) > user_index :
            newargs = list( args )
            newargs[ user_index ] = user
        else:
            raise TypeError( 'Unable to attach authentication argument' )
        
        return newargs, newkw


    # ===========================================
    
    # if a server fails, then send email and remove it from the list!
    def _call_one( self, method, *args, **kwargs ):
        server = self._pick_one()
        ret = None
        try:
            p = xmlrpc_lib.ServerProxy(server, allow_none=True )
            name = method.__name__
            
            argspec = inspect.getargspec(method)
            user_index = argspec.args.index( 'user' ) - 1 
            
            # security protocol replaces username with a full user-credential object:
            servernonce = p.get_nonce()
            username = self._get_user( user_index, args, kwargs )
            user = tuple( auth.get_user_credentials( username, self._conf, servernonce ))
            newargs, newkw = self._set_user( user_index, user, args, kwargs )
            
            # Be careful here, if you mess this call up, you'll be calling the
            # local definition of the server method, not the method on the remote server!
            ret = p.__getattr__(name)(*newargs, **newkw) # do the function call
            
        except socket.error :
            if self._notifier :
                self._notifier( server ) # flash the red lights
            self._server_list.remove( server )
            self._server_bound = len( self._server_list )
            self._server_num = 0
            if not self._server_list:
                raise # pass the socket.error on up
            return self._call_one( method, *args, **kwargs )
        return ret

    # ===========================================
        
    def _call_all( self, method, *args, **kwargs ):
        ret = {}
        
        # would be lovely to execute in parallel:
        for server in self._server_list :
            try:
                p = xmlrpc_lib.ServerProxy(server, allow_none=True )
                name = method.__name__
                
                argspec = inspect.getargspec(method)
                user_index = argspec.args.index( 'user' ) - 1
                
                # security protocol replaces username with a full user-credential object:
                servernonce = p.get_nonce()
                username = self._get_user( user_index, args, kwargs )
                user = tuple( auth.get_user_credentials( username, self._conf, servernonce ))
                newargs, newkw = self._set_user( user_index, user, args, kwargs )
                
                # Be careful here, if you mess this call up, you'll be calling the
                # local definition of the server method, not the method on the remote server!
                ret[ server ] = p.__getattr__(name)( *newargs, **newkw) # do the function call

            except socket.error :
                if self._notifier :
                    self._notifier( server ) # flash the red lights
                self._server_list.remove( server )
                self._server_bound = len( self._server_list )
                self._server_num = 0
                raise # pass the socket.error on up

        return ret

    # ===========================================
      
    @classmethod
    def _rpc_one( cls, fn ):
        def api( client, *args, **kwargs ):
            return client._call_one( fn, *args, **kwargs )
        
        api.__doc__ = fn.__doc__
        setattr( cls, fn.__name__, api )  
        return fn

    # ===========================================
      
    @classmethod
    def _rpc_all( cls, fn ):
        def api( client, *args, **kwargs ):
            return client._call_all( fn, *args, **kwargs )
            
        api.__doc__ = fn.__doc__
        setattr( cls, fn.__name__, api )  
        return fn

    # ===========================================
    
    @classmethod
    def _rpc_specific( cls, fn ):
        argspec = inspect.getargspec(fn)
        submid_index = argspec.args.index( 'submid' ) - 1
        user_index = argspec.args.index( 'user' ) - 1
        
        def api( client, *args, **kwargs ):
            submid = args[submid_index]
            server, server_submid = submid.split( '#', 1 )

            p = xmlrpc_lib.ServerProxy(server, allow_none=True )
            method = p.__getattr__(fn.__name__)                
                
            # security protocol replaces username with a full user-credential object:
            username = client._get_user( user_index, args, kwargs )
            servernonce = p.get_nonce()
            user = tuple( auth.get_user_credentials( username, client._conf, servernonce ))
            newargs, newkw = client._set_user( user_index, user, args, kwargs )

            # Be careful here, if you mess this call up, you'll be calling the
            # local definition of the server method, not the method on the remote server!    
            return method(*newargs, **newkw) # do the function call
          
        api.__doc__ = fn.__doc__
        setattr( cls, fn.__name__, api )
        return fn

# -------------------------------------------------------------------

#
# decorator for methods:
# requires that the class of the method has a method _auth_user_method
# to authorize access to the method
# requires that the method has a parameter 'user' which is a UserCredentials object
#
def _authorized(fn):
    argspec = inspect.getargspec(fn)
    user_index = argspec.args.index( 'user' ) - 1

    def wrapper(server, *args, **kwargs):
      user = args[user_index]      
      if server._auth_user_method( user, fn.__name__ ):
        return fn(server, *args, **kwargs) # do the original function call
      
      return None
    
    return functools.wraps(fn)(wrapper)


# -------------------------------------------------------------------   

# to be executed in a sandbox only!
# Should not be launching processes from a multi-threaded server engine,
# using a sandbox (with processes spawned before the threads were launched,
# you can launch processes safely from there.
# @@ Should probably collect all sandbox function and label them somehow, or decorate them?
# launch_argv_SB ??
def launch_argv (sessionargv) :
    textout = subprocess.check_output(sessionargv, stderr=subprocess.STDOUT)
    return textout

# -------------------------------------------------------------------   


# to be executed in a sandbox only!
def load_document( ccnctx, document ):
    ccnctx.load_doc( document )
    return ccnctx

# -------------------------------------------------------------------

# XMLRPC App, launches a sidecar process (sandbox) immediately,
# so the multiprocessing should occur before a multi-threaded server
# starts making calls to it.  (ref: very bad spawning processes from threads)
class ServerApp : 
  
    def __init__(self, url, parm, logginglevel = logging.DEBUG):
        "parm is the parameter dictionary; contains server configuration vars"
      
        # get a logger:
        self._logger = logging.getLogger('cogserver')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)s | %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logginglevel)
        self._logger.info( "Initializing server app" )
        self._url = url
        # ---------------------------------------
        
        # no default shutdown callable -- needs to come from server framework:
        # server really does need to be shutdown cleanly, 
        # to terminate sidecar processes
        # associated with the sandbox.
        self._shutdown_callable = None # needed to shutdown the server above us
        
        
        # ---------------------------------------
        #
        # get configuration settings:
        #
        self._parm = conf.get_default_server_config()
        for k in parm :
            self._parm[k] = copy.deepcopy(parm[k])

        # ---------------------------------------
        
        # create sandbox before 
        self._sandbox = sandbox.Sandbox() # separate process(es) for safe running of user code
        
        # ---------------------------------------
        
        self._noncecache = {}
        self._noncelock =  threading.Lock()
        
        # ---------------------------------------
        
        self._auth = auth.MethodPermissions( self._parm, self._logger )
        
        # ---------------------------------------
        
        database.check_database(self._parm['COGSERVER_DATABASE'], sql.DATABASE_SCHEMA_LIST)
        self._db = database.Database(self._parm['COGSERVER_DATABASE'], sql.DATABASE_BEGIN)
        
        # ---------------------------------------
        
        self._mutex = threading.Lock()
        
        # ---------------------------------------
        
        # set up the task queue and get it going:
        self._taskq = queue.PriorityQueue() # tuple (datetime, method, parameters)
        # queue up the tasks for the first time:
        self._task(BACKUP_BEGIN, "_task_backup", (self._parm['COGSERVER_BACKUP_INTERVAL'],))
        self._task(SCHEDULE_BEGIN, "_task_schedule", (SCHEDULE_INTERVAL,))
        self._task(MAINTENANCE_BEGIN, "_task_maintenance", (self._parm['COGSERVER_MAINTENANCE_INTERVAL'],))
        # one consumer thread implies that no locks are required.
        self._task_consumer = threading.Thread(target=getattr(self,'_consume_tasks'))
        self._task_consumer.daemon = True
        self._task_consumer.start() 
        # ---------------------------------------
        
        return

    # ===========================================
    # below are the private calls to manage periodic processes
    #
    def _task(self, sec_from_now, name, args):
        # use this to queue work for the consumer thread
        now = datetime.datetime.now()
        when = now + datetime.timedelta(seconds=sec_from_now)
        method = getattr(self,name)
        unique_key = os.urandom(8)
        self._taskq.put(((when, now, unique_key), method, args))
        return


    def _consume_tasks(self):
        # do not call this directly, this is used by the consumer thread.
        # one thread consuming tasks, implies that no locks are required.
        while True:
            item = self._taskq.get()
            self._taskq.task_done()
            
            count = 0
            
            # remove redundant calls (which might occur on bulk loading)
            # minimizes some kinds of bottlenecks, esp when failures are occurring
            if not self._taskq.empty() :
                do_removals = True
                while do_removals:
                    next_item = self._taskq.get()
                    self._taskq.task_done()
                    count += 1
                    if (next_item[1] != item[1]) or (next_item[2] != item[2]) :
                        self._taskq.put(next_item)
                        do_removals = False
                        count -= 1
            
            if count > 0 :
                self._logger.debug('Skip redundant operations (%d)' % count)
            
            if item[0][0] > datetime.datetime.now() :
                self._taskq.put(item)
                time.sleep(0.5)
            else:
                method = item[1]
                args = item[2]
                method(*args)

    # -------------------------------------------------------------------------
    
    def _task_maintenance(self, interval=-1):
        try:
            self._logger.info('Starting database maintenance')
            
            db = self._db.clone()
            if db.sql_begin_exclusive() :
                db.sql_update(sql.VACUUM, [])
                db.sql_end()
            db.sql_begin_write()
            db.sql_update(sql.ANALYZE, [])
            db.sql_end()     
            self._logger.info('End database maintenance')
        except:
            self._logger.error('Exception during database maintenance')
            self._logger.error(traceback.format_exc())
        finally:
            if interval >= 0 :
                self._task(interval, '_task_maintenance', (interval,)) 
        return
    
    # -------------------------------------------------------------------------
    
    def _task_backup(self, interval=-1):
        try:
            self._lock()
            
            backup_path = self._parm['COGSERVER_BACKUPPATH']    
            datafile = self._parm['COGSERVER_DATABASE']
            filename = os.path.basename( datafile )
            
            if os.path.isfile(datafile):
                self._logger.info('Backup: %s' % datafile)
                backup_name = os.path.join(backup_path, '%s.sql.gz' % filename)
                database.backup(datafile, backup_name)
                self._logger.info('Backup Successful')
                   
        except:
            self._logger.error('Exception during backup')
            self._logger.error(traceback.format_exc())
        finally:
            self._unlock()
            if interval >= 0 :
                self._task(interval, '_task_backup', (interval,))  
        return
    
    # -------------------------------------------------------------------------
    
    def _task_schedule(self, interval=-1):
        
        try:
            row = self._get_eligible_submission()

            while row :
                
                submid = str(row[0])
                # @@ priority = int(row[1])
                # @@ title = str( row[2] )
                user = str( row[3] )
                email = str( row[4] )
                document = self._decode_doc( row[5] )
                nodelist = str( row[6] ).split( ',')
                # @@ state = row[7]
                
                userid, groupid = self._auth.get_ids( user )
                assert( userid != 0 )
                assert( groupid != 0 )
                
                # apply changes from previous executions to this document: 
                document.extend( self._get_exec_documents( submid ))
                
                # load the document in a sandbox because it could contain execute code blocks!
                ccnctx = ccn.Context( self._parm )
            
                runnable = sandbox.Runnable( userid, groupid, load_document, (ccnctx, document), {} )
                result = self._sandbox.submit( runnable )
                result = sandbox.RunResult( *result )
                
                if result.exc or not result.ret :
                    raise SyntaxError( result.exc )
                
                ccnctx = result.ret # returned ccn with loaded document.
        
                nodeids = [ccnctx.get_obj( 'node', x ).cogid for x in nodelist ]
                self._run_session( submid, user, email, ccnctx, nodeids )
                
                row = self._get_eligible_submission()
                
        except:
            submid = str(row[0])
            user = str( row[3] )
            
            exc = traceback.format_exc()
            self._logger.error( "Error scheduling %s from %s" % (submid,user) )
            self._logger.error( exc )
            
            db = self._db.clone()
            try:
                db.sql_begin_write()
                self._logger.error( 'fail task_schedule' + traceback.format_exc() ) # @@
                db.sql_insert(sql.INSERT_EXECUTION, (submid,submid,'','',sql.EXEC_STATE_NUM['fail'],'',exc))
                db.sql_insert(sql.INSERT_LOG, (datetime.datetime.now(),submid,self._encode_log("Fail to read submission document")))
                db.sql_update(sql.SUBMISSION_FAIL, (submid,))
            except:
                self._logger.error( traceback.format_exc() )
            finally:
                db.sql_end()

        if interval >= 0 :
            self._task(interval, '_task_schedule', (interval,))  
        return

    # ===========================================
    
    def _get_eligible_submission( self ):
        row = None                      
        db = self._db.clone() # necessary for threading with sqlite
        try:
            db.sql_begin_read()
            # get a random row, so that a bad submission does not permanently clog the queue.
            row = db.sql_selectrow(sql.GET_SCHEDULABLE_SUBM, [])
        except:
            self._logger.error( "Error selecting submission to schedule")
            self._logger.error(traceback.format_exc())
            row = None
        finally:
            db.sql_end()
        return row
    
    # -------------------------------------------------------------------------
    
    def _get_session_argv( self, user, execid, submid, sessionobj ):
            
        # acquire user credentials
        userid, groupid = self._auth.get_ids( user )
        assert( userid != 0 )
        assert( groupid != 0 )                
    
        fullexecid = '%s#%s' % (self._url, execid )
        
        # enter execution into database here, esp so it could be killed later if necessary.
        db = self._db.clone() # necessary for threading with sqlite
        try:    
            db.sql_begin_write()
            db.sql_insert(sql.INSERT_EXECUTION, (execid,submid,sessionobj.cogname,'',sql.EXEC_STATE_NUM['run'],'',None))
            db.sql_update(sql.SUBMISSION_RUN, (submid,))
        except:
            self._logger.error( "Error launching execution %s for submission %s" % (execid,submid))
            self._logger.error(traceback.format_exc())
        finally:
            db.sql_end()
            
            
        # get argv from session object.
        # must run in a sandbox (only) !!
        ccsctx = ccs.Context( sessionobj, fullexecid )
        runnable = sandbox.Runnable( userid, groupid, session.get_argv, ( sessionobj, ccsctx ), {} )
        sessionargv, sessionexc, sessionlog = self._sandbox.submit( runnable )
        
        if sessionexc :
            # fail the execution
            # store exception and log to the database:
            try:    
                db.sql_begin_write()
                self._logger.error( "fail in get session argv" ) # @@
                db.sql_update(sql.EXECUTION_FAIL, (sessionexc, '', execid))
                db.sql_update(sql.SUBMISSION_FAIL, (submid,))
            except:
                self._logger.error( "Error storing failed execution %s" % execid)
                self._logger.error(traceback.format_exc())
            finally:
                db.sql_end()
        else:
            # store argv in the database
            try:    
                db.sql_begin_write()
                db.sql_update(sql.EXECUTION_ARGV, (' '.join(sessionargv),execid))
            except:
                self._logger.error( "Error storing argv(%s) for execution %s" % (' '.join(sessionargv),execid))
                self._logger.error(traceback.format_exc())
            finally:
                db.sql_end()
                
        if sessionlog :
          try:
            db.sql_begin_write()
            db.sql_insert(sql.INSERT_LOG, (datetime.datetime.now(), execid, self._encode_log(sessionlog)))
          except:
            self._logger.error(traceback.format_exc())
          finally:
            db.sql_end()
            
        return sessionargv, sessionexc
    

    # -------------------------------------------------------------------------
    
    def _finish_submission( self, submid, email ) :
            
        # mark the submission as complete in the database
        db = self._db.clone() # necessary for threading with sqlite
        try:    
            db.sql_begin_write()
            db.sql_update(sql.SUBMISSION_DONE, (submid,))
            self._logger.info( "Submission complete %s" % submid )
        except:
            self._logger.error( "Error marking submission done, %s" % submid)
            self._logger.error(traceback.format_exc())
        finally:
            db.sql_end()
            
        # @@ send email to complete the submission

        return

    # -------------------------------------------------------------------------
    
    
    def _run_session( self, submid, user, email, ccnctx, nodeids ) :
        schedule = insp.get_schedule( ccnctx, nodeids )
        
        # out of the entire schedule, get the nodes for the next session:
        sessionnodes = list( itertools.chain( *(schedule.order) ))
        if sessionnodes:
            sessionobj = ccnctx.get_obj_id( sessionnodes[0] ).model.session
            sessionnodes = list( itertools.takewhile( lambda x: ccnctx.get_obj_id( x ).model.session.cogid == sessionobj.cogid, sessionnodes ))
            
            # issue and execid
            execid = uid.pretty_print( uid.create_uid() )
            
            # _get_session_argv also creates an execution entry in the database 
            # and puts the submission and execution in a running state
            sessionargv, exception = self._get_session_argv( user, execid, submid, sessionobj )
            
            # run session argv:
            if not exception and sessionargv and sessionargv[0] :
                # acquire user credentials
                userid, groupid = self._auth.get_ids( user )
                assert( userid != 0 )
                assert( groupid != 0 )
                
                self._logger.info( "Submission %s from %s:\n  %s" % (submid, user, ' '.join(sessionargv)) )
                runnable = sandbox.Runnable( userid, groupid, launch_argv, (sessionargv,), {} )
                result = self._sandbox.submit( runnable )
                result = sandbox.RunResult( *result )
                execlog, execexc, execstdout = result

                if execexc :
                    # fail the execution
                    # store exception and log to the database:
                    db = self._db.clone() # necessary for threading with sqlite
                    try:    
                        db.sql_begin_write()
                        self._logger.error( "fail in run_session" ) # @@
                        db.sql_update(sql.EXECUTION_FAIL, (execexc, '', execid))
                        db.sql_update(sql.SUBMISSION_FAIL, (submid,))
                    except:
                        self._logger.error( "Error storing failed execution %s" % (execid))
                        self._logger.error(traceback.format_exc())
                    finally:
                        db.sql_end()
                else:
                    # data will be stored to the database when the results are returned
                    # by an asynchronous call to apply_results()
                    pass
                  
                if execlog or execstdout :
                    self._logger.error( execlog+execstdout ) # @@
                    db = self._db.clone() # necessary for threading with sqlite
                    try:    
                        db.sql_begin_write()
                        db.sql_insert(sql.INSERT_LOG, (datetime.datetime.now(), execid, self._encode_log(execlog+execstdout)))
                    finally:
                        db.sql_end()

        else:
            # if there are no nodes left to run, let's finish it up!
            self._finish_submission( submid, email )
            
        return
    
    # ===========================================
    
    def _lock(self):
        self._mutex.acquire(True)
        return
        
    def _unlock(self):
        self._mutex.release()
        return    
        
    # ===========================================
    
  
    def __del__(self):
        self._logger.info( "Deallocating server app" )
        
    # ===========================================
    
    def _encode_doc( self, doc ):
        return database.Binary( zlib.compress( json.dumps( doc ) ) )
    
    # -------------------------------------------
    
    def _encode_log( self, log ):
        return database.Binary( zlib.compress( log ) )
        
    # -------------------------------------------
        
    def _decode_doc( self, doc ) :
        return json.loads( zlib.decompress(doc) )
    
    # -------------------------------------------
        
    
    def _decode_log( self, log ) :
        return zlib.decompress( log )
    
    # -------------------------------------------
    
    def _get_exec_submid( self, execid ):
        server, uid = execid.split( '#', 1 )
        submid = None
        db = self._db.clone() # necessary for threading with sqlite
        try:
            db.sql_begin_read()
            submid = db.sql_selectvalue( sql.EXECUTION_SUBMID, (uid,))
        except:
            self._logger.error( "Missing submission id for execution %s" % (uid))
            self._logger.error(traceback.format_exc())
        finally:
            db.sql_end()

        return submid
    
    # -------------------------------------------
    
    def _get_exec_documents( self, submid ):
        document = []
        db = self._db.clone() # necessary for threading with sqlite
        try:     
            db.sql_begin_read()
            rows = db.sql_selectall( sql.EXECUTION_RUNDATA, (submid,))
            if rows :
                document.extend( self._decode_doc(r[0]) for r in rows )
        except:
            raise # @@ can we do better here?
        finally:
            db.sql_end()
        return document

    # -------------------------------------------
    
    @_authorized
    def request_work( self, user, execid ):
        submid = self._get_exec_submid( execid )
        
        document = []
        nodelist = []
        
        # get original document and nodelist from the submission:
        db = self._db.clone() # necessary for threading with sqlite
        try:     
            db.sql_begin_read()
            row = db.sql_selectrow( sql.SELECT_SUBMISSION_RUNDATA, (submid,))
            if row : # @@
                document = self._decode_doc( row[0] )
                nodelist = [ n.strip() for n in row[1].split(',') ]
        except:
            raise # @@ can we do better here?
        finally:
            db.sql_end()
            
        # apply changes from previous executions:
        exec_documents = self._get_exec_documents( submid )
        document.extend( exec_documents )
        
        return document, nodelist
        

    # -------------------------------------------
    

    @_authorized
    def apply_results( self, user, execid, newdoc, log, exc ):
        submid = self._get_exec_submid( execid )
        server, uid = execid.split( '#', 1 )
        
        if exc or not submid:
            # fail the execution in the database:
            db = self._db.clone() # necessary for threading with sqlite
            try:    
                db.sql_begin_write()
                self._logger.error( "fail in apply results" ) # @@
                self._logger.error( exc ) # @@
                self._logger.error( log ) # @@
                self._logger.error( str(newdoc) ) # @@
                self._logger.error( str(execid) ) # @@
                db.sql_update(sql.EXECUTION_FAIL, (exc, newdoc, uid)) # @@ this seems to be failing to write the exception back to the database
                if log :
                    db.sql.insert(sql.INSERT_LOG, (datetime.datetime.now(), uid, self._encode_log(log)))
                if submid :
                    db.sql_update(sql.SUBMISSION_FAIL, (submid,))
            except:
                self._logger.error( "Error storing failed execution %s" % (uid))
                self._logger.error(traceback.format_exc())
            finally:
                db.sql_end()
        else:
            # store log to the database:
            db = self._db.clone() # necessary for threading with sqlite
            try:    
                db.sql_begin_write()
                db.sql_update(sql.EXECUTION_DONE, (self._encode_doc(newdoc), uid))
                if log :
                    db.sql_insert(sql.INSERT_LOG, (datetime.datetime.now(), uid, self._encode_log(log)))
                db.sql_update(sql.SUBMISSION_WAIT, (submid,))
                
            except:
                self._logger.error( "Error storing completed execution %s" % (uid))
                self._logger.error(traceback.format_exc())
            finally:
                db.sql_end()

        return True
    
    # ===========================================

    def get_nonce( self ):
        nonce = base64.b64encode(auth.get_nonce()).encode( "utf-8" )
        now = datetime.datetime.now()
        
        self._noncelock.acquire( True )
        self._noncecache[ nonce ] = now
        self._noncelock.release()
        
        return nonce

    # -------------------------------------------
    
    def _auth_user( self, cred ):
        # prune if past a limit:
        if len( self._noncecache ) > NONCE_CACHE_LIMIT :
            self._noncelock.acquire( True )
            keys = self._noncecache.keys() 
            for k in keys:
                if now - self._noncecache[k] > datetime.timedelta( seconds=NONCE_EXPIRY ) :
                    del self._noncecache[k]
            self._noncelock.release()
        
        # need to verify the server nonce before we call auth module to verify the credentials:
        ret = False
        try:
            self._noncelock.acquire( True )
            timestamp = self._noncecache[ cred.servernonce ]
            if datetime.datetime.now() - timestamp < datetime.timedelta( seconds=NONCE_EXPIRY ):
                del self._noncecache[ cred.servernonce ]
                ret = auth.verify_user_credentials( cred, self._parm )
        finally:
            self._noncelock.release()
        if not ret:
            raise SystemError( "Permission Denied" )
        return ret

    # -------------------------------------------
    
    def _auth_user_method( self, user, methodname ):
        # authenticate the user identity first, then whether they can run the method or not
        # encode from generic tuple from the wire to the named tuple we require
        cred = auth.UserCredentials( *user )
        if self._auth_user( cred ): 
            if self._auth.verify( cred.username, methodname ):
                return True

        raise SystemError( "Permission Denied" )
        return False
    
    
    #############################################
    # ===========================================
    
    # not to be served to clients:
    def set_shutdown_callable(self, fn):
        "Different servers hosting this app need different methods for shutting down"
        self._shutdown_callable = fn

    # ===========================================
    
        
    @_authorized
    @ClientBase._rpc_all
    def shutdown_server(self, user):
        "friendly shutdown of the cluster"
        cred = auth.UserCredentials( *user )
        self._logger.warning( "Shutdown call received from %s" % cred.username )
        self._sandbox.shutdown() # must be called to shut down sidecar processes
        self._lock() # will not release !  # @@ SHOULD PROBABLY WELD THIS TO THE DATABASE MUTEX AND LOCK THAT.
        # @@ ALL database sql_begin_* should take place inside exception block.
        # @@ May be safest to queue the shutdown as a task, so no submissions are in-progress at the time.

        return self._shutdown_callable() # execute the callable


    # ===========================================
    
    
    @_authorized
    @ClientBase._rpc_one
    def submit(self, user, title, document, email, nodes, priority):
        """Submits a document to the server for execution.
        Email should be a fully qualified email address.
        Nodes is a list of nodes in the document to execute.
        returns a submid, which is a http server spec (suitable for RPC) concatenated to a cog_uid, delimited by a hash
        """
        usercred = auth.UserCredentials( *user )
        submid = uid.pretty_print( uid.create_uid() )
        self._logger.info( "Submission %s arrived from %s" % (submid, usercred.username) )
        
        ret = None
        db = self._db.clone() # necessary for threading with sqlite
        try:
            db.sql_begin_write()
            db.sql_insert(
                sql.INSERT_SUBMISSION, 
                (
                    submid,
                    int(priority),
                    str(title),
                    usercred.username,
                    str(email),
                    self._encode_doc(document),
                    ','.join(nodes)
                ))
            ret = '%s#%s' % ( self._url, submid )
        except:
            self._logger.error( "Submission Failure %s, from %s" % (submid, usercred.username))
            self._logger.error(traceback.format_exc())
        finally:
            db.sql_end()
        
        return ret


    # ===========================================
      
    
    @_authorized
    @ClientBase._rpc_all  
    def get_server_list( self, user ): # @@ OK
        return self._url


    # ===========================================
      
    
    @_authorized
    @ClientBase._rpc_all  
    def get_submission_list( self, user ): # @@ OK
        ret = []
        rows = None
        db = self._db.clone() # necessary for threading with sqlite
        try:
            db.sql_begin_read()
            rows = db.sql_selectall(sql.GET_SUBMISSION_LIST, [], column_names=True)
            
        finally:
            db.sql_end()
        
        if rows :
            header = rows[0]
            for r in rows[1:] :
                ret.append( dict(zip( header, r )) )
                
            for d in ret :
                if 'uid' in d :
                    d['uid'] = '%s#%s' % ( self._url, d['uid'] )
                if 'nodelist' in d :
                    d['nodelist'] = [ n.strip() for n in d['nodelist'].split( ',') ]
                if 'document' in d :
                    d['document'] = self._decode_doc( d['document'] )
                if 'state' in d:
                    d['state'] = sql.SUBM_STATE_NAME[ d['state'] ]
                
        return ret


    # ===========================================
      
    @_authorized
    @ClientBase._rpc_specific  
    def get_submission( self, user, submid ): # @@ OK
        ret = []
        rows = None
        server, subm = submid.split('#',1)
        db = self._db.clone() # necessary for threading with sqlite
        try:
            db.sql_begin_read()
            rows = db.sql_selectall(sql.GET_SUBMISSION, (subm,), column_names=True)
            
        finally:
            db.sql_end()
        
        if rows :
            header = rows[0]
            for r in rows[1:] :
                ret.append( dict(zip( header, r )) )
                
            for d in ret :
                if 'uid' in d :
                    d['uid'] = '%s#%s' % ( self._url, d['uid'] )
                if 'nodelist' in d :
                    d['nodelist'] = [ n.strip() for n in d['nodelist'].split( ',') ]
                if 'document' in d :
                    d['document'] = self._decode_doc( d['document'] )
                if 'state' in d:
                    d['state'] = sql.SUBM_STATE_NAME[ d['state'] ]
                    
            if len(ret) == 1:
                ret = ret[0]
        return ret

    # ===========================================

    @_authorized
    @ClientBase._rpc_specific
    def get_submission_log( self, user, submid ): # @@ OK
        ret = []
        rows = None
        server, subm = submid.split('#',1)
        
        db = self._db.clone() # necessary for threading with sqlite
        try:
            db.sql_begin_read()
            rows = db.sql_selectall(sql.GET_SUBM_LOGS, (subm,), column_names=True)

        finally:
            db.sql_end()
            
        if rows :
            header = rows[0]
            for r in rows[1:] :
                ret.append( dict(zip( header, r )) )
                
            for d in ret :
                if 'body' in d :
                    d['body'] = self._decode_log( d['body'] )
                        
        return ret
    
    # ===========================================
    
    @_authorized
    @ClientBase._rpc_specific
    def set_submission_priority( self, user, submid, priority ): # @@ TODO
        
        pass

    # ===========================================
      
    
    @_authorized
    @ClientBase._rpc_specific  
    def kill_submission( self, user, submid): # @@ TODO
        # how can we allow users to kill their own jobs (only) ?  A separate kill_my_submission() ?
        # set kill state on submission
        pass

    # ===========================================
      
    
    @_authorized
    @ClientBase._rpc_specific
    def get_submission_document( self, user, submid, current ): # @@ TODO
        
        pass
    
    # ===========================================

    @_authorized
    @ClientBase._rpc_specific    
    def hold_submission( self, user, submid):
        # TODO @@ # set hold state on submission 
        pass
    
    # ===========================================
   
    @_authorized
    @ClientBase._rpc_specific
    def unhold_submission( self, user, submid) :
        # TODO @@ # unset hold state on submission
        pass
    
      
# -------------------------------------------------------------------

