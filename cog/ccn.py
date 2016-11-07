#####################################################################
#
# Copyright 2015 SpinVFX, 2016 Mayur Patel 
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

from . import conf # configuration module
from . import pr

from .pr import docobject
from .pr import docinfo
from .pr import docio

import copy

# cog code network API : 
# essentially the node-graph construction phase as opposed to the node-graph execution phase

class Context ( object ) :
  
    def __apply_to_store( self, obj ):
        # @@ Should we only save if there's a model?
        # store in indexed formats:
        self._store[ obj.cogid ] = obj
        if obj.cogname :
              self._name_index[ (obj.cogtype, obj.cogname) ] = obj
            

    def get_validated_view( self, document ):        
        """
          Not really for the end user to call - used internally
          
          iterate over a yaml/json/other-serialization data structure, 
            converting dictionaries to objects
          (if they have registered schemas)
          The dict is of the form { 'type name' : { <key-value parameters > } }
          name is optional for some types
          
          If a dictionary is recognized as a potential type
          then the validation method for that type is executed 
          to make sure that the dictionary/datatype is well-formed
          and correct.
          
          If a valid object-store (non-None) is passed to this function,
          then the apply_changes method for that type is executed
          to apply changes to the ccn.
        """
        # @@ consider renaming with an underscore -- if it's not to be exposed!
        
        ret = document
        if docio.do_recognize_schema( document, pr.typenames ): 
            type_name, obj_name = docio.get_view_typename( document )

            view = dict( (y, self.get_validated_view( document[y] )) for y in document )
            ObjClass = pr.classes[ type_name ]
            ObjClass.validate( self, view ) # should throw an exception to reject the object
            
            ret = ObjClass(self, obj_name, view)
          
            ret.apply_changes( self ) # update the ccn state
            
            # apply changes first, before inserting into store 
            # because it might delete conflicting objects already in the store
            self.__apply_to_store( ret ) # store in the ccn
                    
        elif docinfo.is_list( document ):
            ret = [ self.get_validated_view( y ) for y in document ]

        elif docinfo.is_dict( document ) :
            ret = dict( (y, self.get_validated_view( document[y] )) for y in document )
            
        # there can be times where an object is built and then concatenated to the rest of the cnn
        # a good example of this is when a "set" object is used to replace a port on a node.
        elif docinfo.is_object( document ): 
            ret = document
            if ret.cogid not in self._store :
                # this condition should never actually occur
                self.__apply_to_store( ret )

        else:
            ret = copy.deepcopy( document )

        return ret
        
    # =====================================================
  
    def __init__( self, confdict=None ) :
        self._store = {} # key is the unique object id
        self._name_index = {} # key is a tuple (cogtype,cogname)
        
        if confdict is not None:
            self._conf = confdict
        else:
            self._conf = conf.get_default_config()

        
    # -----------------------------------------------------
    
    def get_conf_list( self ):
        return self._conf.keys()
    
    # -----------------------------------------------------
    
    def get_conf( self, name ):
        return self._conf[name] if name in self._conf else None
    
    # -----------------------------------------------------
    
    def has_conf( self, name ):
        return name in self._conf
    
    # -----------------------------------------------------
    
    def get_obj_types( self ):
        return tuple(sorted( pr.typenames ))

    # -----------------------------------------------------
    
    def get_type_order( self ) :
        "returns the order in which types should be processed to avoid causality problems (e.g. links before nodes"
        # resolve order of output:
        order_before = dict( (x, []) for x in pr.typenames )
        for x in pr.typenames :
            bef, aft = pr.classes[ x ].serialize_order()
            if bef:
                assert all( y in pr.typenames for y in bef )
                order_before[ x ].extend( bef )
            if aft:
                for y in aft:
                    assert y in pr.typenames
                    order_before[ y ].append( x )
        # make unique:            
        for x in pr.typenames:
            order_before[x] = set( order_before[x] )
            
        output_order = []
        while order_before :
            count = 0
            keys = list( order_before.keys() ) # make private copy:
            for x in keys:
                if not order_before[x] :
                    output_order.append( x )
                    for y in order_before :
                        if x in order_before[y]:
                            order_before[y].remove( x )
                    del order_before[ x ]
                    count += 1
            if not count:
                raise RuntimeError( "Circular serialization order of document object types: %s" % ','.join(order_before.keys()))
                 
        assert len( output_order ) == len( pr.typenames )
        assert not ( set(output_order) - set( pr.typenames ))
        return tuple(output_order)

    # -----------------------------------------------------
    
    def add_obj( self, objtype, objname, doc ):
        "objdocument is a primitive data structure, remember this is base-level python for network building"
        assert objtype in pr.typenames
        doc = {'%s %s' % (objtype, objname) if objname else '' : doc }
        ret = self.get_validated_view( doc )
        # @@ raise exception on name collision?  Esp relevant to ports
        # that are both redundantly named and have models, also del
        # @@ need to test to verify that the validated object is being returned.
        return ret 
    
    # -----------------------------------------------------

    def get_obj( self, objtype, objname ) :
        "should be tolerant of namespace usage"
        return self._name_index[ (objtype,objname) ]


    # -----------------------------------------------------
      
    def get_obj_id( self, objid ) :
        # need this for links and orders to work -- exposed to the user.
        return self._store[ objid ]
    
    # -----------------------------------------------------
    
      
    def has_obj( self, objtype, objname ) :
        "should be tolerant of namespace usage"
        return (objtype,objname) in self._name_index


    # -----------------------------------------------------
      
    def has_obj_id( self, objid ) :
        # need this for links and orders to work -- exposed to the user.
        return objid in self._store
    
    # -----------------------------------------------------
    
    def rename_obj_id( self, objid, newname ):
        "this renames the given object, but objects that reference it by name may need their views refreshed."
        obj = self._store[ objid ]
        oldname = obj.cogname
        objtype = obj.cogtype
        obj._cogname = newname
        if (objtype,oldname) in self._name_index :
            del self._name_index[(objtype,oldname)]
            self._name_index[(objtype,newname)] = obj
        return
    
    # -----------------------------------------------------
    
    
    def del_obj_id( self, objid):
        # could leave dangling references !
        obj = self.get_obj_id( objid )
        objtype = obj.cogtype
        objname = obj.cogname
        del self._store[objid]
        if objname : # only in name_index if it has a name:
            del self._name_index[ (objtype,objname) ]
        return
      
    # -----------------------------------------------------
    
    def get_obj_if( self, pred_fn ):
        return [ self._store[x] for x in self._store.keys() if pred_fn(self._store[x])]
      
    # -----------------------------------------------------
    
    def del_obj_if( self, pred_fn ):
        keys = [ self._store[x].cogid for x in self._store.keys() if pred_fn(self._store[x])]
        for k in keys:
            self.del_obj_id( k )
        return
      
    # -----------------------------------------------------
    # convenience, so you don't have to read/write the entire document:
    
    def get_attr( self, attrpath ):
        attrlist = attrpath.split('.', 2)
        len_attrlist = len( attrlist )
        if len_attrlist == 1 :
            return [ self._name_index[x] for x in self._name_index.keys() if x[0] == objtype ]
        elif len_attrlist == 2 :
            return docio.get_view_body(self._name_index[(attrlist[0],attrlist[1])].view)  
        else:
            return docio.get_attribute( docio.get_view_body(self._name_index[(attrlist[0],attrlist[1])].view), attrlist[2])

    # -----------------------------------------------------
    
    def get_attr_children( self, attrpath, use_model_fields=False ):
        o = self.get_attr( attrpath )
        return docio.get_doc_children( o, use_model_fields )

    # -----------------------------------------------------
      
    def set_attr( self, attrpath, doc ):
        objtype, objname, objpath = attrpath.split( '.', 2 )
        obj = self._name_index[(objtype,objname)]
        docio.set_attribute( docio.get_view_body( obj.view ), objpath, doc, self )
        obj.update_model(self)

    # -----------------------------------------------------
    # commonly would not use these from within the "script" document:
    
    
    def merge( self, ccn_context ): 
        # potential namespace collisions, unless one of them has had theirs changed.
        self._store.update( ccn_context._store  )
        # rebuild index
        self._name_index = dict( ((self._store[k].cogtype, self._store[k].cogname), self._store[k]) for k in self._store )
        return
      
    # -----------------------------------------------------
    # commonly would not use these from within the "script" document:
    
    def push_namespace( self, ns ):
        # have to build all the renaming first, because renaming deletes elements
        # from the dictionary, invalidating the iteration over that data structure:
        output_order = self.get_type_order()
        # process in dependency order of docobject types:
        for objtype in output_order :
            # get objects of the current type:
            typematch = lambda o : o.cogtype == objtype
            objs = self.get_obj_if( typematch )
            for obj in objs:
                newname = '%s:%s' % (ns, obj.cogname)
                self.rename_obj_id( obj.cogid, newname )
                obj.update_view( self ) # to refresh references to dependencies/objects already renamed.
        return
        
    # -----------------------------------------------------
    def pop_namespace( self ):
        # remember:
        # if the network has been merge, it's possible that different nodes have completely
        # different namespaces, with no leading characters in common.
        output_order = self.get_type_order()
        # process in dependency order of docobject types:
        for objtype in output_order :
            # get objects of the current type:
            typematch = lambda o : o.cogtype == objtype
            objs = self.get_obj_if( typematch )
            for obj in objs:
                parts = obj.cogname.split( ':', 1 )
                if len(parts) != 1 : # some docobjects, like ports, rename themselves to eliminate the namespace            
                    newname = ':'.join(parts[1:])
                    self.rename_obj_id( obj.cogid, newname )
                obj.update_view( self ) # to refresh references to dependencies/objects already renamed.
        return

    # -----------------------------------------------------
    def dump_doc( self ) :
        # convert network to a "document" - a primitive serializable data structure
        output_order = self.get_type_order()
        
        # execute conversion of output:
        ret = []
        for x in output_order :
            # keeping them sorted (by cogid) roughly maintains instantiation order -- just makes it easier to read & debug
            keys = sorted( y for y in self._store.keys() if self._store[y].cogtype == x )
            for y in keys:
                docs = self._store[y].as_docs( self )
                if docs:
                    ret.extend( [ y for y in docs if y] )
        return ret


    # -----------------------------------------------------
    def load_doc( self, doc ):
        # ingest a data structure of primitives (document), erasing any old contents
        self._store = {} # key is the unique object id
        self._name_index = {} # key is a tuple (cogtype,cogname)
        
        return self.get_validated_view( doc )
      

    # -----------------------------------------------------
    
