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

from . import docobject
from . import docinfo
from . import docio

from . import source

class ExecuteObject( docobject.DocObject ):
    _cogtype = 'execute'
    
    def __init__(self, ccn, cogname, view):
        super( ExecuteObject, self ).__init__(ccn, cogname, view)    

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (ExecuteObject._cogtype,) ) :
            view = docio.get_view_body( doc )

            if not docinfo.is_string( view ):
                raise TypeError( "Expected execute object to have a string value" )
            else:
                exec_obj = source.compile_code(  view, 'ccn %s' % ExecuteObject._cogtype) # try compiling it; allow errors to occur
        else:
            raise  TypeError( "Don't recognize schema for execute :\n%s" % str(doc))
        return
 
    def update_model( self, ccn ):
        pass
      
    def update_view( self, ccn ):
        pass
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        
        # compile code
        # compiling code should be a security-safe operation:
        exec_obj = source.compile_code( docio.get_view_body(self.view), 'ccn %s' % self._cogtype)
        
        # execute code
        # executing code needs to be under lock and key:
        source.execute_code( exec_obj, { 'ccn' : ccn })

    def make_dup( self, ccn, newname ):
        # Deep copy of this object, entered into ccn with the new name.
        return None

    def as_docs( self, ccn  ):
        return None

    @staticmethod
    def serialize_order():
        return (None,None)

