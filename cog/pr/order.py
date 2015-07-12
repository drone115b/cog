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

import collections
OrderModel = collections.namedtuple( "OrderModel", ['source','target'])

class OrderObject( docobject.DocObject ):
    _cogtype = 'order'
    
    def __init__(self, ccn, cogname, view):
        super( OrderObject, self ).__init__(ccn, cogname, view)    

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (OrderObject._cogtype,) ) :
            view = docio.get_view_body( doc )
            
            if not docinfo.is_list( view ) or len( view ) != 2:
                msgs.append( "Expected a list of two elements for order object (%s)" % str(view) )
            else:
                dest1 = view[0]
                dest2 = view[1]

                if not (ccn.has_obj( 'node', dest1 ) and ccn.has_obj( 'node', dest2 )):
                    msgs.append( "Unable to reference order targets: %s" % str(view))        
        else:
           msgs.append( "Don't recognize schema for order :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
       
       
    def update_model( self, ccn ):
        "updates model from view"
        view = docio.get_view_body( self.view )
        dest1 = ccn.get_obj( 'node', view[0] )
        dest2 = ccn.get_obj( 'node', view[1] )
        self.model = OrderModel( dest1, dest2 )
      
    def update_view( self, ccn ):
        "updates view from model"
        if self.model:
            view = docio.get_view_body( self.view )
            src = self.model.source
            tgt = self.model.target
            view = [src.cogname, tgt.cogname]
        
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        pass
    
    
    def make_dup( self, ccn, newname ):
        # Deep copy of this object, entered into ccn with the new name.
        return None

        
    def as_docs( self, ccn  ):
        self.update_view(ccn) # catches renames, etc that might have occurred
        return [self.view]

    @staticmethod
    def serialize_order():
        return (('node',),None)

