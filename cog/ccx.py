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

import objport

# in cog execution code : as ccx


class Context( object ) :
    def __init__( self, nodeobj, ccn ) :
        self._node = nodeobj
        assert( self._node and self._node.cogtype == "node" )
        self._changes = []
        self._ccn = ccn
    
    # -----------------------------------------------------
    
    def get_input_list( self ):
        return [ x.cogname for x in self._node.model.inputs ]
    
    # -----------------------------------------------------
        
    def get_input( self, portname ):
        port = objport.get_port_named( self._node, portname, outputs=False)
        if not port:
            raise NameError( "No port named %s in node %s" % (portname, self._node.cogname) )
        return port.model.value

    # -----------------------------------------------------

    def get_output_list( self ) :
        return [ x.cogname for x in self._node.model.outputs ]

    # -----------------------------------------------------

    def set_output( self, portname, value ) :
        self._ccn.set_attr( 'node.%s.outputs.%s.value' %( self._node.cogname, portname), value )
        print( self._ccn.get_attr('node.%s.outputs.%s.value' %( self._node.cogname, portname)) )
        self._changes.append( (portname, value) )
        
    # -----------------------------------------------------

    def get_changes( self ) :
       return self._changes        

    # -----------------------------------------------------

