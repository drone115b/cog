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


class UnlinkObject( docobject.DocObject ):
    _cogtype = 'unlink'
    
    def __init__(self, ccn, cogname, view):
        super( UnlinkObject, self ).__init__(ccn, cogname, view)    

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        from .. import objport
        msgs = []
        if docio.do_recognize_schema( doc, (UnlinkObject._cogtype,) ) :
            view = docio.get_view_body( doc )
            
            if docinfo.is_string( view ):
                try:
                    nodename, portname = view.split('.')
                    np = objport.get_objport_by_name( ccn, nodename, portname )
                    nodeobj = np.obj
                    portobj = np.portobj
                    assert( docinfo.is_object_type( portobj, 'port' ))
                    assert( docinfo.is_object_type( nodeobj, 'node' ))
                except:
                    msgs.append( "Unable to reference unlink target: %s" % str(view))
            else:
                msgs.append( "Expected a string for value of node.port object in unlink: %s" % str(view) )
        else:
           msgs.append( "Don't recognize schema for link :\%sn" % str(doc))

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
        from .. import objport
        view = docio.get_view_body( self.view )
        tgt = view.split('.')
        tgt = objport.get_objport_by_name( ccn, tgt[0], tgt[-1] )
        ccn.del_obj_if( lambda x : x.cogtype == 'link' and x.model.target.obj.cogid == tgt.obj.cogid and x.model.target.portobj.cogid == tgt.portobj.cogid )

    def make_dup( self, ccn, newname ):
        # Deep copy of this object, entered into ccn with the new name.
        return None

    def as_docs( self, ccn  ):
        return None

    @staticmethod
    def serialize_order():
        return (None,None)
