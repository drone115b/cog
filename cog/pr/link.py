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
LinkModelFields = ('source','target')
LinkModel = collections.namedtuple( "LinkModel", LinkModelFields)

class LinkObject( docobject.DocObject ):
    _cogtype = 'link'
    
    def __init__(self, ccn, cogname, view):
        super( LinkObject, self ).__init__(ccn, cogname, view)    

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        from .. import objport
        msgs = []
        if docio.do_recognize_schema( doc, (LinkObject._cogtype,) ) :
            view = docio.get_view_body( doc )
            
            if not docinfo.is_list( view ) or len( view ) != 2:
                msgs.append( "Expected a list of two elements for link object (%s)" % str(view) )
            else:
                dest1 = view[0].split( '.' )
                dest2 = view[1].split( '.' )
                if len( dest1 ) != 2 or len( dest2 ) != 2 :
                    msgs.append( "Port identifier on link does not seem to be a node/port pair" )
                else:
                    try:
                        dest1 = objport.get_objport_by_name( ccn, dest1[0], dest1[-1] )
                        dest2 = objport.get_objport_by_name( ccn, dest2[0], dest2[-1] )
                    except:
                        msgs.append( "Unable to reference link targets: %s" % str(view))        
        else:
           msgs.append( "Don't recognize schema for link :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
       
       
    def update_model( self, ccn ):
        "updates model from view"
        from .. import objport
        view = docio.get_view_body( self.view )
        dest1 = view[0].split( '.' )
        dest2 = view[1].split( '.' )
        dest1 = objport.get_objport_by_name( ccn, dest1[0], dest1[-1] )
        dest2 = objport.get_objport_by_name( ccn, dest2[0], dest2[-1] )
        self.model = LinkModel( dest1, dest2 )
      
    def update_view( self, ccn ):
        "updates view from model"
        if self.model:
            view = docio.get_view_body( self.view )
            src = self.model.source
            tgt = self.model.target
            view[0:] = ["%s.%s" % (src.obj.cogname, src.portobj.cogname), "%s.%s" % (tgt.obj.cogname, tgt.portobj.cogname)]
        
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        ccn.del_obj_if( lambda x : x.cogtype == 'link' and x.model.target.obj.cogid == self.model.target.obj.cogid and x.model.target.portobj.cogid == self.model.target.portobj.cogid ) # remove existing link

    def make_dup( self, ccn, newname ):
        # Deep copy of this object, entered into ccn with the new name.
        return None

    def as_docs( self, ccn  ):
        self.update_view(ccn) # catches renames, etc that might have occurred
        return [self.view]

    @staticmethod
    def serialize_order():
        return (('node','port'),None)

