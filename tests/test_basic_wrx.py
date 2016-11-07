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

class BasicWRX(unittest.TestCase):
  # ----------------------------------------
  
  def setUp(self):
    self.yamldoc = """

- session std1 :
    inputs :
        - port std_version :
            widget_hint : string
            widget_help : Select a version of python to use
            value : python27
    code : |
        ccs.set_argv( ['/home/mayur/cog_session_%s.py' % ccs.get_input('std_version'), ccs.get_execid()] )

- session std2 :
    inputs :
        - port std2_version :
            value : python27
    code : |
        ccs.set_argv( ['/home/mayur/cog_session_%s.py' % ccs.get_input('std2_version'), ccs.get_execid()] )


- op op1 :
    inputs :
        - port op1_filename :
            widget_hint : string
            value : '/tmp/cog/cog.db'
    outputs:
        - port op1_output:
            widget_hint : string
    session : std1
    code : |
        import os
        ccx.set_output( 'op1_output', os.path.dirname( ccx.get_input( 'op1_filename' )))
        
- op op2 :
    inputs :
        - port op2_filename :
            widget_hint : string
    outputs:
        - port op2_output:
            widget_hint : string
            widget_help : I do not know what this thing does
    session : std2
    code : |
        print( "op2 code: %s" % ccx.get_input('op2_filename') )
        ccx.set_output( 'op2_output', ccx.get_input('op2_filename') )

- node node1 : op1
- node node2 : op2

- link : ['node1.op1_output', 'node2.op2_filename']

- ui qt4 :
    node.node1 : [ 21, 45 ]
    node.node2 : [ 56, 78 ]

"""

    self.doc = yaml.load( self.yamldoc )
    self.ccn = cog.ccn.Context()
    self.ccn.load_doc( self.doc )
    
  def test_view1(self):
    obj1 = self.ccn.get_obj( 'node', 'node1' )
    self.assertEqual( obj1.view['node node1']['session'], 'std1' )
    self.assertEqual( obj1.view['node node1']['code'], "import os\nccx.set_output( 'op1_output', os.path.dirname( ccx.get_input( 'op1_filename' )))\n" )
     
  def test_getattr1( self ) :
    self.assertEqual( self.ccn.get_attr( 'node.node2.code' ), """print( "op2 code: %s" % ccx.get_input('op2_filename') )\nccx.set_output( 'op2_output', ccx.get_input('op2_filename') )\n""" )
    self.assertEqual( self.ccn.get_attr( 'node.node1.session' ), 'std1' )
    self.assertEqual( self.ccn.get_attr( 'op.op1.outputs.op1_output.widget_hint' ), 'string' )

  def test_addobj_delobj1(self):
    # add a node and see the number of them increase
    fn =  lambda x : x.cogtype == 'node'
    nodecount = len(self.ccn.get_obj_if( fn ))
    obj1 = self.ccn.add_obj( 'node', 'nodeX', 'op2' )
    self.assertEqual( self.ccn.has_obj( 'node','nodeX' ), True )
    self.assertEqual( len( self.ccn.get_obj_if( fn ) ), nodecount+1 )
    self.assertEqual( self.ccn.get_obj( 'node', 'nodeX' ).model.code, self.ccn.get_obj( 'op', 'op2' ).model.code)
    # test getting that node back:
    oid = obj1.cogid
    obj2 = self.ccn.get_obj_id( oid )
    self.assertEqual( obj1, obj2 )
    # delete that extra node and see everything return
    self.ccn.del_obj_id( oid )
    self.assertEqual( len( self.ccn.get_obj_if( fn ) ), nodecount )     

  def test_pushpop_namespace( self ) :
    self.ccn.push_namespace( 'NMSP1' )
    self.assertEqual( self.ccn.get_attr( 'node.NMSP1:node2.code' ), """print( "op2 code: %s" % ccx.get_input('op2_filename') )\nccx.set_output( 'op2_output', ccx.get_input('op2_filename') )\n""" )
    self.assertEqual( self.ccn.get_attr( 'node.NMSP1:node1.session' ), 'NMSP1:std1' )
    self.assertEqual( self.ccn.get_attr( 'op.NMSP1:op1.outputs.op1_output.widget_hint' ), 'string' )
    self.ccn.push_namespace( 'NMSP2' )
    self.assertEqual( self.ccn.get_attr( 'node.NMSP2:NMSP1:node2.code' ), """print( "op2 code: %s" % ccx.get_input('op2_filename') )\nccx.set_output( 'op2_output', ccx.get_input('op2_filename') )\n""" )
    self.assertEqual( self.ccn.get_attr( 'node.NMSP2:NMSP1:node1.session' ), 'NMSP2:NMSP1:std1' )
    self.assertEqual( self.ccn.get_attr( 'op.NMSP2:NMSP1:op1.outputs.op1_output.widget_hint' ), 'string' )
    self.ccn.pop_namespace()
    self.assertEqual( self.ccn.get_attr( 'node.NMSP1:node2.code' ), """print( "op2 code: %s" % ccx.get_input('op2_filename') )\nccx.set_output( 'op2_output', ccx.get_input('op2_filename') )\n""" )
    self.assertEqual( self.ccn.get_attr( 'node.NMSP1:node1.session' ), 'NMSP1:std1' )
    self.assertEqual( self.ccn.get_attr( 'op.NMSP1:op1.outputs.op1_output.widget_hint' ), 'string' )
    self.ccn.pop_namespace()
    self.test_getattr1()
    
  def test_io1( self ):
    doc = self.ccn.dump_doc()
    # it is possible in python 3.x that the order of the
    # docobjects in the document changes.  Not sure why,
    # but this inconsistency occurs between invokations 
    # of python, which is really scary.  In other words, you can
    # run exactly the same code twice in a row and get different results
    # in each run.  Confirmed in python 3.4.3 and 3.5.2 on
    # Ubuntu 14.04 LTS. A fully unambiguous
    # dependency network, which binds the docobjects to a
    # particular output order is one work-around.  (As of now, is implemented)
    # but it feels like the unit test should not need to depend on this:
    for x in self.doc :
        self.assertTrue( x in doc )
    self.assertEqual( len(doc), len(self.doc) )
    
  def test_setattr1( self ) :
    testword = 'banana'
    hold = self.ccn.get_attr( 'op.op1.outputs.op1_output.widget_hint' )
    self.ccn.set_attr( 'op.op1.outputs.op1_output.widget_hint', testword )
    self.assertEqual( self.ccn.get_attr( 'op.op1.outputs.op1_output.widget_hint' ), testword )
    self.ccn.set_attr( 'op.op1.outputs.op1_output.widget_hint', hold )
    self.assertEqual( self.ccn.get_attr( 'op.op1.outputs.op1_output.widget_hint' ), hold )
     
  def test_getattrchildren1( self ) :
    children = self.ccn.get_attr_children( 'op.op1.inputs.op1_filename' )
    self.assertEqual( set( children ), set(['widget_hint','value']) )

