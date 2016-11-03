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

from . import op
from . import port

import copy
import collections

NodeModelFields = ('inputs','outputs','session','category','widget_help','is_terminal','code','op')
NodeModel = collections.namedtuple( "NodeModel", NodeModelFields)


class NodeObject( docobject.DocObject ):
    _cogtype = 'node'
    
    def __init__(self, ccn, cogname, view):
        super( NodeObject, self ).__init__(ccn, cogname, view)
        
    def __get_namespace( self ):
        return self.cogname.rsplit( ':', 1 )[0] if ':' in self.cogname else ''
        
    @staticmethod
    def __fix_namespace( name, nodens ):
        base = name.rsplit( ':', 1 )[-1]
        return '%s:%s' % (nodens, base) if nodens else base

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (NodeObject._cogtype,) ) :
            view = docio.get_view_body( doc )
            objtype, objname = docio.get_view_typename( doc )
            

            if docinfo.is_string( view ):
                try:
                    obj = ccn.get_obj( 'op', view )
                except:
                    msgs.append( "Unable to reference node target for %s: (op) %s" % (objname, str(view)))
                    
                                 
            # while I fear it will lead to sloppy programming, the node has to be able to accept
            # everything that an op accepts, so that validation passes when a value gets set on it.
            # in scripts, we'll encourage use of node : op notation, but 
            # when scripts resolve and values start getting applied, then nodes are ops.
            elif docinfo.is_dict( view ):
                msgs = op.OpObject.validate_view( view, msgs, objname, ccn, 'node' )
            else: 
                msgs.append( "Expected a string (or op body) for value of node object %s" % objname )

        else:
           msgs.append( "Don't recognize schema for node :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
       
       
    def update_model( self, ccn ):
        "updates model from view"
        view = docio.get_view_body( self.view )
        if docinfo.is_string( view ):
            # need to first convert the view to the expanded copy-of-op view:
            op = ccn.get_obj( 'op', view )

            for x in op.model.inputs + op.model.outputs:
                x.update_view( ccn )

            # ports views should be equivalent to plain documents because they do not contain complex types within themselves.
            nodens = self.__get_namespace()
            inports = [ccn.add_obj('port', self.__fix_namespace(x.cogname,nodens), copy.deepcopy( docio.get_view_body(x.view))) for x in op.model.inputs ]
            outports = [ccn.add_obj('port', self.__fix_namespace(x.cogname,nodens), copy.deepcopy( docio.get_view_body(x.view))) for x in op.model.outputs ]
            session = op.model.session
            category = op.model.category
            is_terminal = op.model.is_terminal
            widget_help = op.model.widget_help
            code = op.model.code
            
            self.model = NodeModel( inports, outports, session, category, widget_help, is_terminal, code, op )
            self.view = { '%s %s' % (self.cogtype, self.cogname) : {} } # reset the basic form of the view.
            self.update_view( ccn )
        else:
            op = self.model.op
            
            inports = view['inputs'] if 'inputs' in view else []
            outports = view['outputs'] if 'outputs' in view else []
            session = view['session'] if 'session' in view else None
            category = op.OpObject.clean_category_name( view['category'] ) if 'category' in view else ''
            widget_help = view['widget_help'] if 'widget_help' in view else ''
            is_terminal = bool( view['is_terminal'] ) if 'is_terminal' in view else False
            if not docinfo.is_object_type( session, 'session' ):
                session = ccn.get_obj( 'session', session )
            code = view['code'] if 'code' in view else None

            self.model = NodeModel( inports, outports, session, category, widget_help, is_terminal, code, op )

      
    def update_view( self, ccn ):
        "updates view from model"
        view = docio.get_view_body( self.view )
        view.clear()
        view['inputs'] = self.model.inputs
        view['outputs'] = self.model.outputs
        if self.model.session :
            view['session'] = self.model.session.cogname
        if self.model.category :
            view['category'] = op.OpObject.clean_category_name( self.model.category )
        if self.model.widget_help :
            view['widget_help'] = self.model.widget_help
        if self.model.is_terminal :
            view['is_terminal'] = '1'
        if self.model.code :
            view['code'] = self.model.code

      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        pass


    # TODO: This implementation could definitely be better.  
    # If only a value changes on one input, then we really
    # should not store all the attributes of all the inputs!
    def as_docs( self, ccn  ):
        ret = []
        if ( not self.gencogid ) or ( not ccn.has_obj_id( self.gencogid )) :
            self.update_view(ccn) # catches renames, etc that might have occurred
            
            set_values = {}
            if self.model.op:
                ret = [{'node %s' % self.cogname : self.model.op.cogname}]
                
                node_parts = sorted(port.serialize( x ) for x in self.model.inputs)
                op_parts = sorted(port.serialize( x ) for x in self.model.op.model.inputs)
                if node_parts != op_parts :
                    set_values['node.%s.inputs' % self.cogname ] = node_parts
                    
                node_parts = sorted(port.serialize( x ) for x in self.model.outputs)
                op_parts = sorted(port.serialize( x ) for x in self.model.op.model.outputs)
                if node_parts != op_parts :
                    set_values['node.%s.outputs' % self.cogname ] = node_parts
                    
                if self.model.op.model.session != self.model.session : # compare python addresses
                    set_values['node.%s.session' % self.cogname] = self.model.session.cogname if self.model.session else ''
                
                if self.model.op.model.category != self.model.category :
                    set_values['node.%s.category' % self.cogname] = self.model.category if self.model.category else ''
                    
                if self.model.op.model.widget_help != self.model.widget_help :
                    set_values['node.%s.widget_help' % self.cogname] = self.model.widget_help if self.model.widget_help else ''
                    
                if self.model.op.model.is_terminal != self.model.is_terminal :
                    set_values['node.%s.is_terminal' % self.cogname] = self.model.is_terminal
                
                if self.model.op.model.code != self.model.code: # compare python addresses
                    set_values['node.%s.code' % self.cogname] = self.model.code if self.model.code else ''
                    
                if set_values:
                    ret.append({'set': set_values})
            
            else:
                
                set_values['inputs'] = [port.serialize( x ) for x in self.model.inputs]
                set_values['outputs'] = [port.serialize( x ) for x in self.model.outputs]
                if self.model.session:
                    set_values['session'] = self.model.session.cogname
                if self.model.category:
                    set_values['category'] = self.model.category
                if self.model.widget_help :
                    set_values['widget_help'] = self.model.widget_help
                if self.model.code:
                    set_values['code'] = self.model.code
                    
                ret = [{'%s %s' % (self._cogtype, self.cogname): set_values}]

        return ret


    @staticmethod
    def serialize_order():
        return (('op','port'),None)

