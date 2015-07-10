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

class DupObject( docobject.DocObject ):
    _cogtype = 'dup'
    
    def __init__(self, ccn, cogname, view):
        super( DupObject, self ).__init__(ccn, cogname, view)    

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (DupObject._cogtype,) ) :
            objtype, objname = docio.get_view_typename( doc )
            view = docio.get_view_body( doc )
            
            assert objtype == DupObject._cogtype
            
            if not objname :
                msgs.append( "No target name given for dup" )

            if not docinfo.is_string( view ):
                msgs.append( "No source name given for dup %s" % objname )
              
            hits = [x for x in ccn.get_obj_if(  lambda y : y.cogname == view)]
            hit_count = len( hits )
            if 0 == hit_count :
                msgs.append( "No source matches name %s in dup %s" % (view, objname))
            if hit_count > 1:
                hit_names = ['(%s,%s)' % (x.cogtype, x.cogname) for x in hits]
                hit_names = ','.join( hit_names )
                msgs.append( "Multiple matches for name %s in dup %s, %s" % (view, objname, hit_names))
        else:
           msgs.append( "Don't recognize schema for dup :\n%s" % str(doc))

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
        hits = [x for x in ccn.get_obj_if(lambda y : y.cogname == value)]
        for obj in hits:
            obj.make_dup( ccn, self.cogname )
            
    def make_dup( self, ccn, newname ):
        # Deep copy of this object, entered into ccn with the new name.
        return None
    
    def as_docs( self, ccn ):
        return None

    @staticmethod
    def serialize_order():
        return (None,None)
