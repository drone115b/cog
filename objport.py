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

from .pr import docinfo

import collections
ObjPort = collections.namedtuple( "ObjPort", ['obj','portobj'])

# some conveniences for working with objects that have ports (sessions, nodes)
  
# get port from the object that contains it, because port names will have
# tons of collisions inside the ccn name index.

def get_port_named( obj, portname, inputs=True, outputs=True ) :
    portlist = []
    if inputs :
        portlist.extend( obj.model.inputs if hasattr( obj.model, 'inputs' ) else [] )
    if outputs : 
        portlist.extend( obj.model.outputs if hasattr( obj.model, 'outputs' ) else [] )
    for x in portlist :
        if x.cogname == portname:
            assert docinfo.is_object_type( x, 'port' )
            return x
    return None
  
def get_port_id( obj, portid, inputs=True, outputs=True ):
    portlist = []
    if inputs:
        portlist.extend( obj.model.inputs if hasattr( obj.model, 'inputs' ) else [])
    if outputs:
        portlist.extend( obj.model.outputs if hasattr( obj.model, 'outputs' ) else [])
    for x in portlist :
        if x.cogid == portid:
            assert docinfo.is_object_type( x, 'port' )
            return x
    return None
  
def get_objport_by_name( ccn, objname, portname, objtype='node' ):
    "returns a tuple of node/port objects"
    obj = ccn.get_obj( objtype, objname )
    return ObjPort( obj, get_port_named( obj, portname ) )
    
def get_objport_by_id( ccn, objid, portid ):
    "returns a tuple of node/port objects"
    obj = ccn.get_obj_id( objid )
    return ObjPort( obj, get_port_id( obj, port_id ) )


