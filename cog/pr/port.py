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

PortModelFields = ('value','widget_hint', 'widget_help')
PortModel = collections.namedtuple( "PortModel", PortModelFields )


class PortObject( docobject.DocObject ):
    _cogtype = 'port'
    
    def __init__(self, ccn, cogname, view):
        super( PortObject, self ).__init__(ccn, cogname, view)
        
    def _strip_namespaces( self ) :
        self._cogname = self._cogname.split( ':' )[-1]   
         
    @staticmethod    
    def is_mutable() :
        # ports can be edited explicity.
        return True
        
    @staticmethod
    def is_operation():
        # by default, objects are things that can be stored and edited.
        return False
        
    @staticmethod
    def has_unique_name():
        # ports do not have unique names, different ops/nodes/sessions could have same-name ports.
        return False
        
    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (PortObject._cogtype,) ) :
            objtype, objname = docio.get_view_typename( doc )
            view = docio.get_view_body( doc )
            
            assert objtype == PortObject._cogtype
            
            if not docinfo.is_dict(view) :
                msgs.append( "Unexpected data type as value for port object" )
                
            else:
                extra_fields = set(view.keys()) - set(PortModelFields)
                if extra_fields :
                    msgs.append( "Unexpected fields on port object: %s" % ','.join(list(extra_fields)))
                    
            # @@ experimental:
            if 'value' not in view:
                view['value'] = None

        else:
           msgs.append( "Don't recognize schema for port :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
      
    def update_model( self, ccn ):
        view = docio.get_view_body( self.view )
        widget_hint = view['widget_hint'] if 'widget_hint' in view else ''
        widget_help = view['widget_help'] if 'widget_help' in view else ''
        value = view['value'] if 'value' in view else None
        self._strip_namespaces()
        self.model = PortModel( value, widget_hint, widget_help )
      
    def update_view( self, ccn ):
        view = docio.get_view_body( self.view )
        view.clear()
        if self.model.widget_hint :
            view['widget_hint'] = self.model.widget_hint
        if self.model.widget_help :
            view['widget_help'] = self.model.widget_help
        if self.model.value is not None:
            view['value'] = self.model.value
        self._strip_namespaces()
        self.view = {"%s %s" % (self.cogtype, self.cogname) : view }
              
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        pass

    def copy_to( self, from_ccn, to_ccn ):
        # Copy this object to a new ccn; should check for dependencies in the new ccn.
        # ports can't be duplicated directly, because they need to live in a container - the container needs to be duplicated.
        return None

    def as_docs( self, ccn ):
        return None # no need to write to document, defined in-line with ops & nodes

    @staticmethod
    def serialize_order():
        return (None,None)
    

def serialize( portobj ):
    """We don't use the as_docs() method because that would not un-embed
    the port from its container object; but we do need this function
    to serialize the port on behalf of the objects that contain it."""
    view = {}
    if portobj.model.widget_hint:
        view[ 'widget_hint' ] = portobj.model.widget_hint
    if portobj.model.widget_help:
        view[ 'widget_help' ] = portobj.model.widget_help
    if portobj.model.value is not None :
        view[ 'value' ] = portobj.model.value
    return { '%s %s' % (portobj.cogtype, portobj.cogname) : view }
