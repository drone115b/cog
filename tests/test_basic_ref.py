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

# ==========================================

try:
    import ruamel.yaml as yaml
except:
    import yaml

# ==========================================

import cog.ccn

# ==========================================

class BasicRef(unittest.TestCase):

  def setUp(self):
    os.chdir( os.path.dirname( __file__ ) )
    filename = 'test_basic_ref_002.yaml'
    yamldoc = open( filename, 'rt' ).read()
    self.doc = yaml.load( yamldoc )
    self.ccn = cog.ccn.Context()
    self.ccn.load_doc( self.doc )
    
  def test_view1(self):
    obj1 = self.ccn.get_obj( 'node', 'node1' )
    self.assertEqual( obj1.view['node node1']['session'], 'std:sess1' )
    self.assertEqual( obj1.view['node node1']['code'], "import os\nccx.set_output( 'op1_output', os.path.dirname( ccx.get_input( 'op1_filename' )))\n" )
    
  def test_io( self ) :
    doc = self.ccn.dump_doc()
    self.assertEqual( self.doc, doc )

