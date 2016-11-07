#####################################################################
#
# Copyright 2015 SpinVFX, 2016 Mayur Patel 
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

from .. import uid

"""
This module defines base classes used to implement various document objects types.
"""

class DocObjectType(type):
    _registry = {}
    def __init__(cls, name, bases, attrs):
        if hasattr( cls, '_cogtype' ) and cls._cogtype :
            DocObjectType._registry[cls._cogtype] = cls
        return super(DocObjectType, cls).__init__(name, bases, attrs)



__class_body = """    
%s    
        _cogtype = None # overload this

        def __init__(self, ccn, cogname, view, generatorid=None) :
            self._cogname = cogname
            self._view = view
            
            self._cogid = uid.create_uid()
            
            self._model = None
            self.update_model( ccn )
            
            #
            # if the object is created by a reference or other procedural
            # object, then there are some operations that do not need
            # to be performed on it, such as as_docs().
            # Objects need to be aware of the cogid of the object that
            # generated them procedurally, if applicable:
            #
            self._generatorid = generatorid
            return
        
        @staticmethod    
        def is_mutable() :
            # by default, object parameters can be edited:
            return True
            
        @staticmethod
        def is_operation():
            # by default, objects are things that can be stored and edited.
            # though sometimes you will have object types that operate on the ccn
            # then 'go away'
            return False
            
        @staticmethod
        def has_unique_name():
            # by default, objects have unique names
            return True
            
        @staticmethod
        def is_generator():
            # by default, objects don't create other objects as part of their application to the ccn
            return False
            
        def get_model_fields( self ):
            return self._model._fields if hasattr( self._model, "_fields" ) else None
    
        @property
        def view( self ) :
            return self._view
            
        @view.setter
        def view( self, x ):
            self._view = x
        
        @property
        def model( self ) :
            return self._model
            
        @model.setter
        def model( self, x ):
            self._model = x
        
        @property
        def cogtype( self ):
            return self._cogtype

        @property
        def cogname( self ):
            return self._cogname
            
        @property
        def cogid( self ):
            return self._cogid

        @property
        def gencogid( self ) :
            return self._generatorid
            
        @gencogid.setter
        def gencogid( self, x ):
            # only to be called by the object doing the generation of self!
            self._generatorid = x

        @staticmethod
        def validate( ccn, obj ) :
            # Should throw an exception if the document is not properly-formed for the type in question otherwise should pass
            raise NotImplementedError('')
            
        def update_model( self, ccn ):
            raise NotImplementedError('')
            
        def update_view( self, ccn ):
            raise NotImplementedError('')
            
        def apply_changes( self, ccn ):
            # Should apply changes to the objstore (ObjectStore) according to its function.
            raise NotImplementedError('')
            
        def copy_to( self, from_ccn, to_ccn ):
            # Copy this object to a new ccn; should check for dependencies in the new ccn.
            self.update_view(from_ccn) # catches renames, etc that might have occurred
            view = list(self.view.items())[0][1] # should call docio.get_view_body( self.view ), but can't resolve scopes properly in both python2 and python3
            obj = to_ccn.add_obj( self.cogtype, self.cogname, view )
            return obj
            
        def delete_generated( self, ccn ):
            # delete all the other objects that this one created as part of it's 'generation'
            # by default, objects are not generators; but this is a generic implementation for all
            if self.is_generator() :
                # delete all the other objects that this one created as part of it's 'generation'
                # by default, objects are not generators.
                output_order = ccn.get_obj_type_order()
                output_order = output_order.reverse() # delete in reverse chronological order
                genmatch = lambda x : x.gencogid == self.cogid
                objs = ccn.get_obj_if( genmatch ) # find objects generated by self
                keys = sorted( y.cogid for y in objs ).reverse() # keys of generated objects in reverse chronological order
                keys = [ y for y in keys if ccn.has_obj_id( y ) ] # filter out any objects already deleted by other means
                for x in output_order :
                    objs = [ y for y in keys if ccn.get_obj_id( y ).cogtype == x ]
                    for y in objs:
                        obj = ccn.get_obj_id( y )
                        if obj.is_generator() :
                            obj.delete_generated( ccn )
                        ccn.del_obj_id( y )
            return
            
        @classmethod
        def rm_from( cls, ccn, doc ) :
            # Delete an object from a ccn, could leave dangling references; but deletes
            # anything it generated in addition to the object itself.
            # the default implementation assumes that the 'doc' is a unique cogname:
            # This is really to support the "rm" docobject, not for general use.
            ret = False
            if ccn.has_obj( cls._cogtype, doc ) :
                obj = ccn.get_obj( cls._cogtype, doc )
                if obj.is_generator() :
                    obj.delete_generated( ccn )
                ccn.del_obj_id( obj.cogid )
                ret = True
            return ret
            
        @classmethod
        def validate_rm_doc( cls, ccn, obj ):
            # During parsing, check that the parameters to the deletion are valid:
            # the default implementation assumes that the 'doc' is a unique cogname:
            # This is really to support the "rm" object, not for general use.
            if not docinfo.is_string( obj ):
                raise TypeError('Expected string for rm ' + cls._cogtype + ' not document: ' + str(obj))                

        def as_docs( self, ccn ):
            # convert from whatever the objstore has stored, to a document (list of objects) suitable for writing out.
            # If the object is generated by application of another object (like a reference) then the generating
            # object needs to take responsibility for storing any changes made to the generated object.
            raise NotImplementedError('')

        @staticmethod
        def serialize_order():
            return( None, None )"""


# need to wrap class declaration into an exec call in order to be able to catch syntax error exceptions
# which will be thrown because of the differences between python 3 and python 2 syntax
try:
    exec( __class_body % "class DocObject( metaclass=DocObjectType ) :" )
except SyntaxError:
    exec(__class_body % 'class DocObject( object ) :\n        __metaclass__ = DocObjectType')
 

#################################################

def get_classes():
    return DocObjectType._registry 
  
def get_class( objtype ):
     return DocObjectType._registry[ objtype ]


