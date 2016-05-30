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

OpModelFields = ('inputs','outputs','session','category','widget_help','is_terminal','code')
OpModel = collections.namedtuple( "OpModel", OpModelFields)


class OpObject( docobject.DocObject ):
    _cogtype = 'op'
    
    def __init__(self, ccn, cogname, view):
        super( OpObject, self ).__init__(ccn, cogname, view)
        
    #staticmethod
    def clean_category_name( self, cat ):
        return '/'.join( x.strip().lower() for x in cat.split('/') if x.strip() )

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (OpObject._cogtype,) ) :
            view = docio.get_view_body( doc )
            objtype, objname = docio.get_view_typename( doc )
            
            msgs = OpObject.validate_view( view, msgs, objname, ccn )
            
        else:
           msgs.append( "Don't recognize schema for op :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
       

    @staticmethod 
    def validate_view( view, msgs, objname, ccn, typename='op' ):
        if not docinfo.is_dict( view ):
            msgs.append( "Expected fields (dict/map) for %s object (%s), found %s" % (str(type(view)), objname, typename))
        else:
            extra_fields = set( view.keys() ) - set(OpModelFields)
            if extra_fields :
                msgs.append( "Object %s has unrecognized fields: %s" % (objname, ','.join(list(extra_fields))))
                
            for x in ( 'inputs', 'outputs' ):
                if x in view :
                    if not docinfo.is_list( view[x] ):
                        msgs.append( "Object %s are not in a list in %s" % (x, objname) )
                    else:
                        if not all( docinfo.is_object_type( y, 'port' ) for y in view[x] ):
                            msgs.append( "Object are not all valid ports in %s.%s" % (objname,x) )
                    
            if 'session' in view:
                if docinfo.is_string( view['session'] ):
                    if not ccn.has_obj('session', view['session'] ) :
                        msgs.append( "Could not find session %s for %s.%s" % (view['session'], typename, objname))
                else:
                   msgs.append( "Expected string to indicate session for type %s named %s" % (typename, objname))
                
            if 'code' in view:
                if docinfo.is_string( view['code'] ):
                    exec_obj = source.compile_code( view['code'], '%s %s' % (typename, objname))
                else:
                    msgs.append( "Object code item is not a string, in %s.%s" % (typename, objname))

            if 'category' in view:
                if not docinfo.is_string( view['category'] ):
                    msgs.append( "Category not a string, in %s.%s" % (typename, objname) )
                    
            if 'widget_help' in view:
                if not docinfo.is_string( view['widget_help'] ) :
                    msgs.append( "Widget_help not a string, in %s.%s" % (typename, objname))

        return msgs

       
    def update_model( self, ccn ):
        "updates model from view"
        view = docio.get_view_body( self.view )
        inports = view['inputs'] if 'inputs' in view else []
        outports = view['outputs'] if 'outputs' in view else []
        session = view['session'] if 'session' in view else None
        category = self.clean_category_name( view['category'] ) if 'category' in view else ''
        widget_help = view['widget_help'] if 'widget_help' in view else ''
        is_terminal = bool(view['is_terminal']) if 'is_terminal' in view else False
        if not docinfo.is_object_type( session, 'session' ):
            session = ccn.get_obj( 'session', str(session) )
        code = view['code'] if 'code' in view else None

        self.model = OpModel( inports, outports, session, category, widget_help, is_terminal, code )


    def update_view( self, ccn ):
        "updates view from model"
        view = docio.get_view_body( self.view )
        view = {}
        view['inputs'] = self.model.inputs
        view['outputs'] = self.model.outputs
        if self.model.session :
            view['session'] = self.model.session
        view['category'] = self.clean_category_name( self.model.category )
        view['widget_help'] = self.model.widget_help
        view['is_terminal'] = self.model.is_terminal
        if self.model.code :
            view['code'] = self.model.code

      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        pass
    
    
    def make_dup( self, ccn, newname ):
        # Deep copy of this object, entered into ccn with the new name.
        oldname = self.cogname
        doc = self.as_docs(ccn)[0]
        view = docio.get_view_body( doc )
        return ccn.add_obj( self._cogtype, newname, view )
        
    
    def as_docs( self, ccn  ):
        self.update_view(ccn) # catches renames, etc that might have occurred
        
        set_values = {}
        set_values['inputs'] = [port.serialize( x ) for x in self.model.inputs]
        set_values['outputs'] = [port.serialize( x ) for x in self.model.outputs]
        if self.model.session:
            set_values['session'] = self.model.session.cogname
        if self.model.category:
            set_values['category'] = self.model.category
        if self.model.widget_help :
            set_values['widget_help'] = self.model.widget_help
        if self.model.is_terminal :
            set_values['is_terminal'] = '1'
        if self.model.code:
            set_values['code'] = self.model.code
            
        ret = [{'%s %s' % (self._cogtype, self.cogname) : set_values}]
            
        return ret


    @staticmethod
    def serialize_order():
        return (('session',),None)

