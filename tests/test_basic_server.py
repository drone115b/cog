#####################################################################
#
# Copyright 2016 Mayur Patel
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

# ==========================================

import unittest
import os
import socket

try:
    from xmlrpc.server import SimpleXMLRPCServer
except:
    from SimpleXMLRPCServer import SimpleXMLRPCServer 


try:
    import SocketServer as socketserver
except:
    import socketserver

# ==========================================

try:
    import ruamel.yaml as yaml
except:
    import yaml

# ==========================================

import cog.ccn
import cog.server
import cog.conf
import cog.client

# ==========================================

class SimpleThreadedXMLRPCServer(socketserver.ThreadingMixIn, SimpleXMLRPCServer):
        pass

# ------------------------------------------


def get_url() :
    return "http://%s:8084" % socket.getfqdn()

# ------------------------------------------

def launch_server() :
    # technically the server should run as root
    config = cog.conf.get_default_server_config()

    config['COG_SCRIPTPATH'] = '/tmp'
    config['COG_AUTHPATH'] = '/tmp'
    config[ 'COGSERVER_CLEANUP_INTERVAL' ] = 60 * 2 # 2 minutes
    config[ 'COGSERVER_ARCHIVE_INTERVAL' ] = 60 * 10 # 10 minutes
    config[ 'COGSERVER_PERMISSIONS_EXPIRY' ] = 60 * 15 # 15 minutes
    config[ 'COGSERVER_DATABASE' ] = os.environ.get( 'COGSERVER_DATABASE', '/tmp/cog.db' )
    config[ 'COGSERVER_BACKUP_INTERVAL' ] = int(os.environ.get( 'COGSERVER_BACKUP_INTERVAL', 60 * 4 )) # 4 minutes
    config[ 'COGSERVER_BACKUPPATH' ] = os.environ.get( 'COGSERVER_BACKUPPATH', '/tmp' )

    url = get_url()
    server, port = url.rsplit(':',1)
    if server.startswith('http://'):
        server = server[7:]
    if server.startswith('https://'):
        server = server[8:]
    xmlrpc_app = cog.server.ServerApp(url, config)
    xmlrpc_server = SimpleThreadedXMLRPCServer( (server, int(port)), allow_none=True )
    xmlrpc_server.register_instance( xmlrpc_app )
    
    xmlrpc_app.set_shutdown_callable(xmlrpc_server.shutdown)
    xmlrpc_server.serve_forever()
    raise SystemExit(0)

# ------------------------------------------

def shutdown_server() :
    url = get_url()

    conf = cog.conf.get_default_config()
    conf['COG_SERVERS'] = url
    conf['COG_AUTHPATH'] = '/tmp'

    client = cog.client.Client( conf )
    client.shutdown_server( '' )

# ==========================================

class BasicServer(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    os.chdir( os.path.dirname( __file__ ) )
    cls._pid = os.fork()
    if cls._pid == 0 :
        try:
            launch_server()
        except SystemExit:
            raise unittest.SkipTest("No testing in server process")

  @classmethod
  def tearDownClass(cls):
    if cls._pid :
      shutdown_server()


  def setUp(self):
    filename = 'test_basic_server_002.cog'
    yamldoc = open( filename, 'rt' ).read()
    self.doc = yaml.load( yamldoc )
    self.ccn = cog.ccn.Context()
    self.ccn.load_doc( self.doc )
    
  def test_001(self):
    self.assertEqual( True, True ) # @@

