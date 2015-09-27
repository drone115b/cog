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

import traceback

try: # version-proof
    import xmlrpc.client as xmlrpc_lib
except ImportError :
    import xmlrpclib as xmlrpc_lib

from . import conf
from . import ccx
from . import ccn
from . import capture
from . import pr
from .pr import source
from . import auth
from . import objport 

# to be run in a sandbox only!
def run( execid, config=None ):
    newdoc, log, exc = [], [], None
    
    c = config if config else conf.get_default_config()
    
    server, uid = execid.split('#',1)
    p = xmlrpc_lib.ServerProxy(server, allow_none=True )
    
    servernonce = p.get_nonce() 
    usercred = auth.get_user_credentials( auth.get_username(), config, servernonce )
    doc, nodes = p.request_work( tuple(usercred), execid ) # authenticated
    
    if doc and nodes :
        ccnctx = ccn.Context( c )
        ccnctx.load_doc( doc )
    
        for nodename in nodes :
            # catch streams:
            with capture.StreamCapture() as output:
                try :
                    nodeobj = ccnctx.get_obj( 'node', nodename )
                    ccxctx = ccx.Context( nodeobj, ccnctx )
                    
                    # execute node here, no sandbox required:
                    
                    # compile code
                    # compiling code should be a security-safe operation:
                    exec_obj = source.compile_code( nodeobj.model.code, 'node %s' % nodename)
                    
                    # execute code
                    # executing code needs to be under lock and key:
                    source.execute_code( exec_obj, { 'ccx' : ccxctx })
                    
                    # record resulting values:
                    changes = ccxctx.get_changes()
                    change_dict = dict( ('node.%s.outputs.%s.value' % (nodeobj.cogname, portname), value) for portname, value in changes )
                    newdoc.append( {'set': change_dict } )
                    for attr in change_dict :
                        ccnctx.set_attr( attr, change_dict[ attr ] )
                    
                    # find the links to whom we need to distribute calculated values:
                    fn_findlinks = lambda obj : obj.cogtype == 'link' and obj.model.source.obj.cogid == nodeobj.cogid
                    linkobjs = ccnctx.get_obj_if( fn_findlinks ) # expensive
                    
                    # apply calculated values across these links to the target nodes:
                    change_dict_targets = {}
                    for portname, value in changes :               
                        portobj = objport.get_objport_by_name( ccnctx, nodeobj.cogname, portname )
                        for obj in linkobjs : 
                            if obj.model.source.obj.cogid == nodeobj.cogid and obj.model.source.portobj.cogid == portobj.portobj.cogid :
                                change_dict_targets[ 'node.%s.inputs.%s.value' % (obj.model.target.obj.cogname, obj.model.target.portobj.cogname) ] = value
                    if change_dict_targets :
                        newdoc.append( { 'set' : change_dict_targets } )
                        for attr in change_dict_targets :
                            ccnctx.set_attr( attr, change_dict_targets[ attr ] )
                    
                except:
                    # record resulting exception:
                    exc = traceback.format_exc()
                    break # for each node
                
            log.extend( output.getvalue() ) # @@ SHOULD WRITE BACK LOGS AS THEY ARE AVAILABLE.
            
        servernonce = p.get_nonce() 
        usercred = auth.get_user_credentials( usercred.username, config, servernonce )
        p.apply_results( tuple(usercred), execid, newdoc, '\n'.join(log), exc ) # authenticated
    return

