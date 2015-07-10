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

class UnorderObject( docobject.DocObject ):
    _cogtype = 'unorder'
    
    def __init__(self, ccn, cogname, view):
        super( UnorderObject, self ).__init__(ccn, cogname, view)    

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (UnorderObject._cogtype,) ) :
            view = docio.get_view_body( doc )
            
            if not docinfo.is_list( view ) or len( view ) != 2:
                msgs.append( "Expected a list of two elements for unorder object" )
            else:
                if not ccn.has_obj( 'node', view[0] ):
                    msgs.append( "Node (%s) on order unobject cannot be found" % view[0])
                if not ccn.has_obj( 'node', view[1] ):
                    msgs.append( "Node (%s) on order unobject cannot be found" % view[1])        
        else:
           msgs.append( "Don't recognize schema for unorder :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
       
    def update_model( self, ccn ):
        "updates model from view"
        pass
      
    def update_view( self, ccn ):
        "updates view from model"
        pass
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        view = docio.get_view_body(self.view)
        objid1 = ccn.get_obj( 'node', view[0]).cogid
        objid2 = ccn.get_obj( 'node', view[1]).cogid
        ccn.del_obj_if( lambda x : x.cogtype == 'order' and x.model.source.cogid == objid1 and x.model.target.cogid == objid2 )

    def make_dup( self, ccn, newname ):
        # Deep copy of this object, entered into ccn with the new name.
        return None

    def as_docs( self, ccn  ):
        return None

    @staticmethod
    def serialize_order():
        return (None,None)
