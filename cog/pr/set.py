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

class SetObject( docobject.DocObject ):
    _cogtype = 'set'
    
    def __init__(self, ccn, cogname, view):
        super( SetObject, self ).__init__(ccn, cogname, view)    
        
    @staticmethod    
    def is_mutable() :
        # set cannot be edited explicity, delete and recreate them.
        return False
        
    @staticmethod
    def is_operation():
        # set object types operate on the ccn then 'go away'
        return True
        
    @staticmethod
    def has_unique_name():
        # set objects do not have unique names
        return False
        
    @staticmethod
    def __get_obj_name_attr( attrpath ):
       attrlist = attrpath.split( '.', 2 )
       assert len(attrlist) > 2
       return ( attrlist[0], attrlist[1], attrlist[2] )

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (SetObject._cogtype,) ) :
            objtype, objname = docio.get_view_typename( doc )
            view = docio.get_view_body( doc )
            
            assert objtype == SetObject._cogtype
            
            if not docinfo.is_dict( view ):
                msgs.append( "Expected a dictionary/map for set values" )
            else:
                for k in view:
                    try:
                        objtype, objname, attrpath = SetObject.__get_obj_name_attr( k )
                        if '.' in attrpath : # verify parent of attribute to set, can't verify value itself as it might be optional.
                            parent = attrpath.split( '.', 1 )[0]
                            obj = docio.get_attribute( ccn.get_obj(objtype,objname), parent)
                            
                            if not obj:
                                msgs.append( "Could not find attribute: %s (set)" % k )
                    except:
                        msgs.append("Error accessing attribute: %s (set)" % view[k])
            
        else:
           msgs.append( "Don't recognize schema for set :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
      
    def update_model( self, ccn ):
        pass
      
    def update_view( self, ccn ):
        pass
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        value = docio.get_view_body(self.view)
        for k in value:
            try:
                ccn.set_attr( k, value[k] )
            except KeyError :
                # it is possible that a set command is issued against a path to a reference
                # that is no longer valid.
                # let's be tolerant of that.
                pass
        
    def copy_to( self, from_ccn, to_ccn ):
        # Copy this object to a new ccn; should check for dependencies in the new ccn.
        # stored as part of the objects that were affected
        return None
        
    @classmethod
    def rm_from( cls, ccn, doc ) :
        # Delete an object from a ccn, could leave dangling references!
        # Does not make sense for set objects
        return False
        
    @classmethod
    def validate_rm_doc( cls, ccn, obj ):
        # During parsing, check that the parameters to the deletion are valid:
        return

    def as_docs( self, ccn ):
        # stored as part of the objects that were affected
        return None

    @staticmethod
    def serialize_order():
        return (None,None)
