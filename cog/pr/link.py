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
    def is_mutable() :
        # links cannot be edited explicity, delete and recreate them.
        return False
        
    @staticmethod
    def is_operation():
        # by default, objects are things that can be stored and edited.
        return False
        
    @staticmethod
    def has_unique_name():
        # links do not have unique names
        return False
            
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
            src = self.model.source
            tgt = self.model.target
            view = ["%s.%s" % (src.obj.cogname, src.portobj.cogname), "%s.%s" % (tgt.obj.cogname, tgt.portobj.cogname)]
            self.view = { "link" : view }
        
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        ccn.del_obj_if( lambda x : x.cogtype == 'link' and x.model.target.obj.cogid == self.model.target.obj.cogid and x.model.target.portobj.cogid == self.model.target.portobj.cogid ) # remove existing link


    @classmethod
    def rm_from( cls, ccn, doc ) :
        # Delete an object from a ccn, could leave dangling references!
        # the link implementation assumes that the 'doc' is a target port name, in the form "objtype.objname.portname":
        ret = False
        objtype, objname, portname = doc.split( '.', 2 )
        target = objport.get_objport_by_name( ccn, objname, portname, objtype )
        if target :
            ret = True
            ccn.del_obj_if( lambda x : x.cogtype == 'link' and x.model.target.obj.cogid == target.obj.cogid and x.model.target.portobj.cogid == target.portobj.cogid )
        return ret


    @classmethod
    def validate_rm_doc( cls, ccn, obj ):
        # During parsing, check that the parameters to the deletion are valid:
        # the link implementation assumes that the 'doc' is a target port name, in the form "objtype.objname.portname":
        msgs = []
        if docinfo.is_string( obj ) :
            parts = obj.split('.')
            if not parts[0] in ( 'node', 'session' ) :
                msgs.append( "Expected node or session in link rm: %s" % obj )
            else:
                if len( parts ) != 3 :
                    msgs.append( "Expected rm link value of the form: objtype.objname.portname" )
            # doesn't need to resolve to a specific port - useful for keeping it robust 
            # with nested references that might be changing.
        else:
           msgs.append( "Expected a string for rm link :\n%s" % str(obj) )
        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
        
        
    def as_docs( self, ccn  ):
        ret = []
        if ( not self.gencogid ) or ( not ccn.has_obj_id( self.gencogid )) :
            self.update_view(ccn) # catches renames, etc that might have occurred
            ret = [self.view]
        return ret

    @staticmethod
    def serialize_order():
        return (('node','port'),None)

