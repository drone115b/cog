#####################################################################
#
# Copyright 2016 Mayur Patel 
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

def getClassCmdNodeCreate( qt ):

    class CmdNodeCreate ( qt.QtGui.QUndoCommand ) :
    
        def _calc_nodename( self, opname, ccn ): # @@ performance CBB
            count = 1
            objname = "{0}{1:03}".format(opname, count)
            while ccn.has_obj( 'node', objname ):
                count += 1
                objname = "{0}{1:03}".format(opname, count)
            return objname
            
    
        def __init__( self, ccn, opname, nodename=None ) :
            self._nodename = nodename if nodename and not cnn.has_obj('node', nodename) else self._calc_nodename( opname, ccn )
            self._opname = opname
            self._ccn = ccn
            self._obj = None
            qt.QtGui.QUndoCommand.__init__( self, "Create {0} ({1})".format(self._nodename, opname) )
        
        
        def redo( self ) :
            self._obj = self._ccn.add_obj(self._opname, self._nodename, {} )
            assert self._obj is not None
        
        
        def undo( self ) : 
            self._ccn.del_obj_id( self._obj.cogid )
            self._obj = None
        
    return CmdNodeCreate

