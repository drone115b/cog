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

        def __init__(self, ccn, cogname, view) :
            self._cogname = cogname
            self._view = view
            
            self._cogid = uid.create_uid()
            
            self._model = None
            self.update_model( ccn )
            return
    
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
            
        def make_dup( self, ccn, newname ):
            # Deep copy of this object, entered into ccn with the new name.
            raise NotImplementedError('')

        def as_docs( self, ccn ):
            # convert from whatever the objstore has stored, to a document (list of objects) suitable for writing out.
            raise NotImplementedError('')

        @staticmethod
        def serialize_order():
            return( None, None )"""


# @@ if True : # @@ try:
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


