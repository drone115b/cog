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

import sys

# version proof
if sys.version_info[0] == 2 :
    cast = unicode
else:
    cast = str
    

# I hate to do this, but I'm having too many problems 
# with python 3 io.StringIO versus python 2 io.BytesIO() etc etc
class StrIO :
    def __init__(self) :
        self._text = []
    def write( self, b ) :
        self._text.append( cast(b) )
    def close( self ) :
        return
    def getvalue(self):
        return cast('').join( self._text )
    def flush(self):
        return


# reference : # http://stackoverflow.com/questions/1817695/python-how-to-get-stringio-writelines-to-accept-unicode-string/1819009#1819009
# reference : http://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
# http://stackoverflow.com/questions/616645/how-do-i-duplicate-sys-stdout-to-a-log-file-in-python
#
# python 3.4 contextlib library apparently deprecates this:
# LEFT OFF HERE : 

#   This may not be thread safe -- is that what's screwing us up here? # @@
class StreamCapture(object):
    def __init__( self, streambuffer=None ):
        if not streambuffer:
            self._buffer = StrIO()
        else:
            self._buffer = streambuffer
    def __enter__(self):
        import sys
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self._buffer
        sys.stderr = self._buffer
        return self
    def __exit__(self, *args):
        import sys
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        self._buffer.flush()
    def getvalue(self):
        ret = [cast(x) for x in self._buffer.getvalue().splitlines()]
        return ret