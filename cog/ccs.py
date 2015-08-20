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

from . import objport

# cog session context:
class Context( object ):
    def __init__( self, sessionobj, execid ):
        self._session = sessionobj
        assert( self._session and self._session.cogtype == "session" )
        self._argv = []
        self._execid = execid
        
    def get_execid( self ) :
        return self._execid
        
    def get_input_list( self ):
        return [ x.cogname for x in self._session.model.inputs ]
        
    def get_input( self, portname ):
        port = objport.get_port_named( self._session, portname)
        if not port:
            raise NameError( "No port named %s in session %s" % (portname, self._session.cogname))
        return port.model.value
    
    def set_argv( self, argvlist ):
        self._argv = argvlist[:]

    def get_argv( self ):
        if not self._argv :
            raise RuntimeError( "No argv set in session %s" % self._session.cogname )
        return self._argv
    