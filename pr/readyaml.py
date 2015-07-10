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

import yaml

import os

class ReadyamlObject( docobject.DocObject ):
    _cogtype = 'readyaml'
    
    def __init__(self, ccn, cogname, view):
        super( ReadyamlObject, self ).__init__(ccn, cogname, view)    

    # ----------------------------------------------------------------------------  
    @staticmethod
    def __resolve_filename( filespec, ccn ):
        resolved = os.path.expandvars( filespec )
        if not os.path.isfile( resolved ):
            scriptpath = ccn.get_conf( 'COG_SCRIPTPATH' )
            if scriptpath :
                pathlist = (x for x in scriptpath.split( os.pathsep ) if os.path.isdir( x ))
                for x in pathlist :
                    candidate = os.path.join( x, resolved )
                    if os.path.isfile( candidate ):
                        resolved = candidate
                        break # for
        return resolved

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (ReadyamlObject._cogtype,) ) :
            view = docio.get_view_body( doc )
            
            if not docinfo.is_string( view ):
                raise TypeError( "Expected readyaml object to have a string value" )
            else:
                filename = ReadyamlObject.__resolve_filename( view, ccn )
                if not os.path.isfile( filename ):
                    raise TypeError( "Readyaml object cannot see file: %s" % filename )

        else:
           msgs.append( "Don't recognize schema for readyaml :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
      
    def update_model( self, ccn ):
        pass
      
    def update_view( self, ccn ):
        pass
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        value =  docio.get_view_body(self.view)
        filename = self.__resolve_filename( value, ccn )
        yaml_doc = open( filename, 'rt' ).read()
        yaml_doc = yaml.safe_load( yaml_doc )
        import cog.ccn
        new_ccn = cog.ccn.Context()
        new_ccn.load_doc( yaml_doc )
        
        namespace = self.cogname
        if namespace:
            new_ccn.push_namespace( namespace )

        ccn.merge( new_ccn )

    def make_dup( self, ccn, newname ):
        # Deep copy of this object, entered into ccn with the new name.
        return None

    def as_docs( self, ccn ):
        return None

    @staticmethod
    def serialize_order():
        return (None,None)
