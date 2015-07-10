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

import threading
try: # python version-proof
    import queue
except:
    import Queue as queue
import time

class Multilock :
    """One writer, unlimited readers, and the option of an exclusive lock
    which will hold off both readers and writers (and will only acquire
    when neither readers nor writers are active)."""
    def __init__(self) :
        self._write = threading.Lock()
        self._read = queue.Queue(1)
        self._read.put(0)
        
    def acquire_read(self):
        self._read.put(self._read.get() + 1)
        self._read.task_done()
        
    def release_read(self):
        self._read.put(self._read.get() - 1)
        self._read.task_done()
        
    def acquire_write(self):
        return self._write.acquire()
        
    def release_write(self):
        self._write.release()
        
    def acquire_exclusive(self, timeout=None):
        if timeout is None:
            expiry = None
        else:
            expiry = time.time() + timeout
            
        succeed = False
        i = -1
        try:
            while not succeed :
                now = time.time()
                if expiry is not None:
                    if now < expiry :
                        break # exit while
                    i = self._read.get(timeout=now - expiry)
                else:
                    i = self._read.get()
                self._read.task_done()
                
                succeed = (0 == i)
                if not succeed :
                   self._read.put(i)

        except:
            succeed = False
            
        if succeed:
            assert self._read.empty()
            succeed = self.acquire_write()
            if not succeed :
                self._read.put(0)
        
        return succeed

    def release_exclusive(self):
        assert self._read.empty()
        write.release()
        self._read.put(0)
