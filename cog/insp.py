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


from . import ccn

from .pr import docinfo
from .pr import docio

import collections
import itertools

# inspect module needs to access the store object explicitly:

def get_dependencies( ccn ):
    "returns a dict where the key is a node cogid and the value are the node cogids that should be executed before it."
    before = {}
   
    # links are explicit dependencies:
    links = ccn.get_obj_if( lambda x : x.cogtype == 'link' ) # list of docobjects
    for x in links:
        if x.model.target.obj.cogid in before :
            before[ x.model.target.obj.cogid ].add( x.model.source.obj.cogid)
        else:
            before[x.model.target.obj.cogid ] = set([ x.model.source.obj.cogid ])
            

    # orders are implicit dependencies - they may not share data,
    # but they are "ordered" to run together.
    orders = ccn.get_obj_if( lambda x : x.cogtype == 'order' ) # list of docobjects
    for x in orders:
        if x.model.target.cogid in before :
            before[ x.model.target.cogid ].add( x.model.source.cogid )
        else:
            before[ x.model.target.cogid ] = set([ x.model.source.cogid ])
      
    return before
    


def get_sessions( ccn, nodeid_list ):
    "returns a dictionary, where the keys are session cogids, and the values are iterables containing the nodes in that session"
    sessions = {}
    for x in nodeid_list:
        n = ccn.get_obj_id(x)
        if n.model.session :
            if n.model.session.cogid in sessions:
                sessions[ n.model.session.cogid ].add( n.cogid )
            else:
                sessions[ n.model.session.cogid ] = set([n.cogid])    
    return sessions


Schedule = collections.namedtuple( "Schedule", ['sessions','order'] )  
def get_schedule( ccn, nodeid_list ):
    """Returns a named tuple, Schedule:
    Schedule.sessions is a dictionary whose keys are the sessions necessary to execute
       and the values are iterables containing the cogid of the nodes in that session.
    Schedule.order is a list of <list of nodeid>, which gives the execution order.  
        Notice that all nodes clustered in the same inner list can (theoretically) be executed in parallel
    """
    
    # get explicit link dependencies:
    dep = get_dependencies( ccn )
    
    # list of required nodes
    req_nodes = set()
    process_list = nodeid_list[:] # shallow copy of input node list
    while process_list :
        x = process_list.pop()
        obj = ccn.get_obj_id( x )
        assert obj.cogtype == 'node'
        # if any of x's outputs are not set, then continue else break
        if any(port.model.value is None for port in obj.model.outputs):
            if x in dep and not x in req_nodes:
                process_list.extend( dep[x] )
            req_nodes.add( x )
    # req_nodes is now the set of nodes (their cogids) that we need to produce the requested output.
    
    # now apply order constraints to nodes:
    # (Note these are not constraints from the 'order' object, but rather
    # all constraints that pertain to dependencies in the execution order of nodes.)
    order_constr = ccn.get_obj_if( lambda x : x.cogtype == 'order' ) # list of docobjects
    order = dict( (x,set( y for y in dep[x] if y in req_nodes )) for x in dep if x in req_nodes ) # dependent nodes should be in req_nodes too!
    for x in order_constr:
        if x.model.source.cogid in req_nodes and x.model.target.cogid in req_nodes:
            order[ x.model.target.cogid ].add( x.model.source.cogid )
            
    # find sessions from among the nodes we require:
    # sessions[ session_cogid ] = set( cogid for nodes in the session )
    #
    sessions = get_sessions( ccn, req_nodes )
    
    #
    # add session constraints to nodes,
    # essentially, each node in the session inherits the upstream and downstream 
    # links/dependencies of every other node in that session.
    # This has the net effect of clustering the nodes of the session together;
    # however, it doesn't mean that other non-session nodes that could be run concurrently
    # with the session do not make it into the same inner list as some session nodes,
    # in the execution order result.
    #
    session_order = dict((x,set([])) for x in sessions)
    for x in req_nodes:
        obj = ccn.get_obj_id( x )
        if obj.model.session and obj.cogid in order : 
            session_order[ obj.model.session.cogid ] |= order[ obj.cogid ]
    # remove nodes from the session_order that are actually in the session:
    for x in session_order :
        session_order[x] = session_order[x] - sessions[x] 
    
    # Now, session_order contains all the nodes that should come before the session.
    for x in sessions:
        for y in sessions[x]: # for the nodes in the session:
            # add the requirements of the session to the requirements of the session's node.
            if y in order :
                order[ y ] |= session_order[x] 
            else:
                order[ y ] = session_order[x]
    
    # Now all the nodes in the session have their orders updated to include all the nodes that come before the session.
    for x in req_nodes:
        for y in sessions:
            # if node requires any part of the session and is not in the session
            if order[x].intersection( sessions[y] ) and not x in sessions[y]:
                # then add all the parts of the sessions as requirements for the node:
                order[ x ].update( sessions[y] )
    # Now all nodes that come after sessions have their orders updated to include all nodes in those sessions.

    ordered_nodes = []
    while order :
        # find all the nodes with no dependencies
        runnables = set( k for k in order if not order[k] ) 
        # remove references to these nodes from the store:
        for k in runnables :
            del order[k]
        for k in order :
            order[k] -= runnables
        # queue them up: they can all run in parallel:    
        ordered_nodes.append( list(runnables) )
        # if there were no hits, then we have a circular dependency:
        count = len( runnables )
        if not count:
            raise RuntimeError( "Circular dependency detected in cog node network: %s" % ','.join([ccn.get_obj_id(x).cogname for x in order]))

    return Schedule( sessions, ordered_nodes )

    
GraphInputs = collections.namedtuple( "GraphInputs", ['sessionport','nodeport'] )
def get_missing_inputs( ccn, schedule ):
    "Given a schedule object (from the get_schedule() call), find missing inputs and returns a GraphInputs object indicating what they are"
    
    nodeid_list = list(itertools.chain( *(schedule.order) ))
    nodeobjs = dict([ (x, ccn.get_obj_id(x)) for x in nodeid_list ])
    assert( all( nodeobjs[x] for x in nodeobjs ) )
    assert( all( docinfo.is_object_type( nodeobjs[x], 'node' ) for x in nodeobjs))
       
    nodeport = set()
    sessionport = set()
       
    # from node definitions, there will be inputs not defined.
    
    for x in nodeid_list:
        node_obj = nodeobjs[ x ]
        if node_obj.model.inputs:
            for port_obj in node_obj.model.inputs:
               if port_obj.model.value is None:
                   nodeport.add( (node_obj.cogid, port_obj.cogid) )
                   
    # there will be some links that have values linked from elsewhere in the graph:
    links = ccn.get_obj_if( lambda x : x.cogtype == 'link' ) # list of docobjects
    nodeport = nodeport - set([tuple(x.model.target) for x in links])
    
    # Now find session inputs:
    for x in schedule.sessions:
        session_obj = ccn.get_obj_id( x )
        assert(docinfo.is_object_type( session_obj, 'session' ))
        for port_obj in session_obj.model.inputs:
            if port_obj.model.value is None:
                sessionport.add( (session_obj.cogid, port_obj.cogid) )
    
    return GraphInputs( sessionport, nodeport )
