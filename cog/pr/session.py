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

from . import source
from . import port

import collections

SessionModelFields = ('inputs','widget_help','code')
SessionModel = collections.namedtuple( "SessionModel", SessionModelFields)


class SessionObject( docobject.DocObject ):
    _cogtype = 'session'
    
    def __init__(self, ccn, cogname, view):
        super( SessionObject, self ).__init__(ccn, cogname, view)

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (SessionObject._cogtype,) ) :
            view = docio.get_view_body( doc )
            objtype, objname = docio.get_view_typename( doc )
            
            msgs = SessionObject.validate_view( view, msgs, objname, ccn )
            
        else:
           msgs.append( "Don't recognize schema for session :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
       

    @staticmethod 
    def validate_view( view, msgs, objname, ccn ):
        typename = SessionObject._cogtype
        if not docinfo.is_dict( view ):
            msgs.append( "Expected fields (dict/map) for %s object (%s), found %s" % (str(type(view)), objname, typename))
        else:
            extra_fields = set( view.keys() ) - set(SessionModelFields)
            if extra_fields :
                msgs.append( "Object %s has unrecognized fields: %s" % (objname, ','.join(list(extra_fields))))
                
            if 'inputs' in view :
                if not docinfo.is_list( view['inputs'] ):
                    msgs.append( "Object inputs are not in a list in %s" % objname)
                else:
                    if not all( docinfo.is_object_type( y, 'port' ) for y in view['inputs'] ):
                        msgs.append( "Object are not all valid ports in %s.inputs" % objname )
                        
            if 'widget_help' in view:
                if not docinfo.is_string( view['widget_help'] ) :
                    msgs.append( "Expected string for widget_help in %s.%s" % (typename, objname))
           
            if 'code' in view:
                if docinfo.is_string( view['code'] ):
                    exec_obj = source.compile_code( view['code'], '%s %s' % (typename, objname))
                else:
                    msgs.append( "Object code item is not a string, in %s.%s" % (typename, objname))
            else:
                msgs.append( "Object requires code field, in %s.%s" % (typename, objname))
        return msgs

       
    def update_model( self, ccn ):
        "updates model from view"
        view = docio.get_view_body( self.view )
        inports = view['inputs'] if 'inputs' in view else []
        widget_help = view['widget_help'] if 'widget_help' in view else ''
        code = view['code'] 
        self.model = SessionModel( inports, widget_help, code )


    def update_view( self, ccn ):
        "updates view from model"
        view = {}
        view['inputs'] = self.model.inputs
        view['widget_help'] = self.model.widget_help
        view['code'] = self.model.code
        self.view = { "%s %s" % (self.cogtype, self.cogname) : view }
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        pass

        
    def as_docs( self, ccn  ):
        ret = []
        if ( not self.gencogid ) or ( not ccn.has_obj_id( self.gencogid )) :
            self.update_view(ccn) # catches renames, etc that might have occurred
            
            set_values = {}
            set_values['inputs'] = [port.serialize( x ) for x in self.model.inputs]
            if self.model.widget_help :
                set_values['widget_help'] = self.model.widget_help
            set_values['code'] = self.model.code
                
            ret = [{'%s %s' % (self._cogtype, self.cogname) : set_values}]
            
        return ret


    @staticmethod
    def serialize_order():
        return (None,None)



def get_argv( sessionobj, ccs ):
    # this function to run in a sandbox only.
    
    # compile code
    # compiling code should be a security-safe operation:
    exec_obj = source.compile_code( sessionobj.model.code, 'session %s' % sessionobj.cogname)
    
    # execute code
    # executing code needs to be under lock and key:
    source.execute_code( exec_obj, { 'ccs' : ccs })
    
    return ccs.get_argv()
