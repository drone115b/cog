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


from . import docobject
from . import docinfo
from . import docio

try: 
    import ruamel.yaml as yaml
except:
    import yaml

import os
import collections

RefyamlModelFields = ('name',)
RefyamlModel = collections.namedtuple( "RefyamlModel", RefyamlModelFields )

class RefyamlObject( docobject.DocObject ):
    _cogtype = 'refyaml'
    
    def __init__(self, ccn, cogname, view):
        super( RefyamlObject, self ).__init__(ccn, cogname, view)
        self._index = {} # key, value := id in referenced file, id in referencing ccn.
        
    @staticmethod    
    def is_mutable() :
        # refs cannot be edited explicity, delete and recreate them.
        return False
        
    @staticmethod
    def is_operation():
        # refs are things that can be stored but not edited.
        return False
        
    @staticmethod
    def has_unique_name():
        # refs do have unique names
        return True
        
    # ----------------------------------------------------------------------------  
    @staticmethod
    def resolve_filename( name, ccn ):
        resolved = os.path.expandvars( name )
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
        
    def get_ref_ccn( self, ccn ) :
        value =  docio.get_view_body(self.view)
        filename = self.resolve_filename( value, ccn )
        yaml_doc = open( filename, 'rt' ).read()
        yaml_doc = yaml.safe_load( yaml_doc )
        import cog.ccn
        refccn = cog.ccn.Context()
        refccn.load_doc( yaml_doc )
        return refccn

    # ----------------------------------------------------------------------------  

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (RefyamlObject._cogtype,) ) :
            view = docio.get_view_body( doc )
            
            if not docinfo.is_string( view ):
                raise TypeError( "Expected refyaml object to have a string value" )
            else:
                filename = RefyamlObject.resolve_filename( view, ccn )
                if not os.path.isfile( filename ):
                    raise TypeError( "Refyaml object cannot see file: %s" % filename )

        else:
           msgs.append( "Don't recognize schema for refyaml :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
      
    def update_model( self, ccn ):
        view = docio.get_view_body( self.view )
        self.model = RefyamlObjectModel( view )
      
    def update_view( self, ccn ):
        self.view = self.model.name
        
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        refccn = self.get_ref_ccn( self, ccn )
        self._index = {}
        
        namespace = self.cogname
        if namespace:
            refccn.push_namespace( namespace )
            
        output_order = refccn.get_obj_type_order()
        # duplicate each object in order by type:
        for x in output_order :
            # get objects of the current type:
            typematch = lambda x : x.cogtype == x
            objs = refccn.get_obj_if( typematch )
            # process objects roughly in the chronological order that they were created:
            keys = sorted( obj.cogid for obj in objs )
            for y in keys:
                obj = refccn.get_obj_id( y )
                if not obj.gencogid : # objects that are going to be regenerated do not need to be copied
                    newobj = obj.copy_to( ccn, refccn )
                    newobj.gencogid = self.cogid # mark new obj as a generated object, made by this reference object
                    self._index[ y ] = newobj.cogid

        return
        
        
    def delete_generated( self, ccn ):
        # delete all the other objects that this one created as part of it's 'generation'
        # override default method, hopefully improves efficiency
        output_order = ccn.get_obj_type_order()
        output_order = output_order.reverse() # delete in reverse chronological order
        keys = sorted( self._index.keys() ).reverse() # keys of generated objects in reverse chronological order
        keys = [ y for y in keys if ccn.has_obj_id( y ) ] # filter out any objects already deleted by other means
        for x in output_order :
            objs = [ y for y in keys if ccn.get_obj_id( y ).cogtype == x ]
            for y in objs:
                obj = ccn.get_obj_id( y )
                if obj.is_generator() :
                    obj.delete_generated( ccn )
                ccn.del_obj_id( y )
        return
        
    def as_docs( self, ccn ):
        self.update_view(ccn) # catches renames, etc that might have occurred
        view = docio.get_view_body( self.view )
        ret = [{'%s %s' % (self._cogtype, self.cogname): view}]
        return ret

    @staticmethod
    def serialize_order():
        return (None,('session','op','node','ui','set','rm'))


