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


import collections
import os
import multiprocessing
import threading
import sys
import pickle
import signal

from .. import capture

Runnable = collections.namedtuple( "Runnable", ['uid','gid','callable','args', 'kwargs'])
RunResult = collections.namedtuple( "RunResult", ['ret','exc', 'stdout'] )


def _do_callable( runnable ):
    "changes the user and group id of the process"
    ret = None
    exc = None
    exc_traceback = None
    stdout = ''
    try:
        # catch streams:
        with capture.StreamCapture() as output:
            os.setresuid( runnable.uid,runnable.uid,runnable.uid )
            os.setresgid( runnable.gid,runnable.gid,runnable.gid )
            ret = runnable.callable( *(runnable.args), **(runnable.kwargs) )        

        stdout = '\n'.join( output.getvalue() )
    except:
        exc_type, exc, exc_traceback = sys.exc_info()
        ret = None

    return RunResult( ret, exc, stdout ) # must be pickle-able, as it will travel between processes
  

def _run_callable_from_q( q ):
    os.setsid() # create a new process session with this process as the leader, makes it easy to kill it and all its child processes.
    runnable = q.get()
    ret = _do_callable( runnable )
    q.put( tuple(ret) )


def _spawn_runnable( runnable, qpid ):
    q = multiprocessing.queues.SimpleQueue()
    q.put( runnable)

    p = multiprocessing.Process(target=_run_callable_from_q, args=(q,))
    p.start()
    
    qpid.put( p.pid )
    p.join()
    try:
        qpid.get(block=False)
    except multiprocessing.Queue.Empty :
        pass
    
    if q.empty() :
        ret = tuple([None, None, '']) # can happen on a crash, abort, sys.exit(), os._exit(), etc etc
    else:
        ret = q.get()
    return ret


class Sandbox( object ):
    def __init__(self):
        self._q_out = multiprocessing.Queue()
        self._q_in = multiprocessing.Queue()
        self._q_pid = multiprocessing.Queue()
        self._threadlock = threading.Lock()
        
        self._p = None
        self._startup() 
        return
        
    def _startup( self ) :
        if not self._p or not self._p.is_alive():
            self._threadlock.acquire()
            try :
                self._p = multiprocessing.Process(target=self._consume_q, args=(self._q_out,self._q_in,self._q_pid))
                self._p.start()
            finally :
                self._threadlock.release()
            
    def _consume_q( self, qsub, qret, qpid ):
        while True:
          try:
            runnable = qsub.get()
            if not runnable :
                return # poison pill design pattern to halt the process
            qret.put( _spawn_runnable( runnable, qpid ) )
          except:
            import traceback
            print( traceback.format_exc() ) # @@ is this the best way to do this?
            qret.put( tuple([None, None, '']))
        
    def shutdown( self ):
        "must be called to shutdown sidecar processes"
        self._threadlock.acquire()
        try:
            self._q_out.put( None ) # poison pill design pattern to halt the process
            if self._p :
                self._p.join()
        finally:
            self._threadlock.release()

    def submit( self, runnable ):
        # does block, run one at a time.
        ret = RunResult( None, None, '')
        self._startup()
        self._threadlock.acquire()
        try:
            s = pickle.dumps( runnable ) # try to trigger an exception earlier rather than later
            if runnable:
                # user must never be allowed to insert 
                # a runnable whose boolean value resolves to False
                # otherwise will interfer with the poison pill shutdown
                
                # do not allow processes to run as root:
                if 0 == runnable.uid or 0 == runnable.gid :
                    raise SystemError( "Permission Denied" )
                
                self._q_out.put( runnable )
                ret = self._q_in.get()
        finally:
            self._threadlock.release()
        return ret


    def kill( self ):
        try:
            pid = self._q_pid.get(block=False)
            if pid not in (0,1):
                os.killpg( pid, signal.SIGKILL ) # more aggressive than TERM, will not allow graceful shutdown
        except multiprocessing.Queue.Empty :
            pass
