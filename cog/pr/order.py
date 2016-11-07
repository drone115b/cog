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

OrderModelFields = ('source','target')
OrderModel = collections.namedtuple( "OrderModel", OrderModelFields)

class OrderObject( docobject.DocObject ):
    _cogtype = 'order'
    
    def __init__(self, ccn, cogname, view):
        super( OrderObject, self ).__init__(ccn, cogname, view)    
    
    @staticmethod    
    def is_mutable() :
        # orders cannot be edited explicity, delete and recreate them.
        return False
        
    @staticmethod
    def is_operation():
        # by default, objects are things that can be stored and edited.
        return False
        
    @staticmethod
    def has_unique_name():
        # orders do not have unique names
        return False

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
            self.view = { 'order' : view }
        
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        pass


    @classmethod
    def rm_from( cls, ccn, doc ) :
        # Delete an object from a ccn, could leave dangling references!
        # the order implementation assumes that the 'doc' is a list of node names, in the form [ 'nodename1', 'nodename2' ]:
        ret = False
        nodename1, nodename2 = doc[:2] # first two items in the list
        if nodename1 and nodename2 :
            ret = True
            ccn.del_obj_if( lambda x : x.cogtype == 'order' and x.model.source.cogname == nodename1 and x.model.target.cogname == nodename2 )
        return ret


    @classmethod
    def validate_rm_doc( cls, ccn, obj ):
        # During parsing, check that the parameters to the deletion are valid:
        # the order implementation assumes that the 'doc' is a list of node names, in the form [ 'nodename1', 'nodename2' ]:
        msgs = []
        if docinfo.is_list( obj ) :
            parts = obj.split('.')
            if len( parts ) != 2 or any( not docinfo.is_string( x ) for x in parts ) :
                    msgs.append( 'Expected rm order value of the form: [ "nodename1", "nodename2" ], not:\n%s' % str(obj) )
        else:
           msgs.append( "Expected a list for rm order :\n%s" % str(obj) )
        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
        
        
        ret = docinfo.is_list( obj ) and ( len( obj ) == 2 ) and ( docinfo.is_string( x ) for x in obj )
        return ret


    def as_docs( self, ccn  ):
        ret = []
        if ( not self.gencogid ) or ( not ccn.has_obj_id( self.gencogid )) :
            self.update_view(ccn) # catches renames, etc that might have occurred
            ret = [self.view]
        return ret
        

    @staticmethod
    def serialize_order():
        return (('node',),None)

