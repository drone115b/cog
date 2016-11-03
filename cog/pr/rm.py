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


from . import docobject
from . import docinfo
from . import docio

class RmObject( docobject.DocObject ):
    _cogtype = 'rm'
    
    def __init__(self, ccn, cogname, view):
        super( RmObject, self ).__init__(ccn, cogname, view)
            
    @staticmethod    
    def is_mutable() :
        # rm cannot be edited explicity, delete and recreate them.
        return False
        
    @staticmethod
    def is_operation():
        # rm object types operate on the ccn then 'go away'
        return True
        
    @staticmethod
    def has_unique_name():
        # rm objects do not have unique names
        return False

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (RmObject._cogtype,) ) :
            objtype, objname = docio.get_view_typename( doc )
            view = docio.get_view_body( doc )
            
            assert objtype == RmObject._cogtype
            
            if objname in docobject.get_classes() :
                objclass = docobject.get_class( objname )
                objclass.validate_rm_doc( ccn, view )
            else:
                msgs.append( "Unrecognized type for removal: %s" % objname )
            
        else:
           msgs.append( "Don't recognize schema for rm :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
      
    def update_model( self, ccn ):
        pass
      
    def update_view( self, ccn ):
        pass
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        objdoc = docio.get_view_body(self.view)
        objclass = docobject.get_class( self.cogname )
        objclass.rm_from( ccn, objdoc )
        return
        
    def copy_to( self, from_ccn, to_ccn ):
        # Copy this object to a new ccn; should check for dependencies in the new ccn.
        # Should not be implemented, the deletion is instant so does not need to be stored.
        return None
        
    @classmethod
    def rm_from( cls, ccn, doc ) :
        # Delete an object from a ccn, could leave dangling references!
        # Does not make sense for rm objects
        return False
        
    @classmethod
    def validate_rm_doc( cls, ccn, obj ):
        # During parsing, check that the parameters to the deletion are valid:
        # Cannot delete a rm object.
        return

    def as_docs( self, ccn ):
        # Should not be implemented, the deletion is instant so does not need to be stored.
        return None

    @staticmethod
    def serialize_order():
        return (None,None)
