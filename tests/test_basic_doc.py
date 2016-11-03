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

import cog.pr.docio as docio
import cog.pr.docinfo as docinfo

# ==========================================

import unittest
import os

# ==========================================

class BasicDoc(unittest.TestCase):
  def test_docdiff1( self ):
    docA = { "hello": "dolly" }
    docB = [ "hello", "dolly" ]
    diff = docio.get_doc_diff( docA, docB )
    self.assertEqual( diff.equal, [] )
    self.assertEqual( diff.unequal, [''] )
    self.assertEqual( diff.missing, [] )
    self.assertEqual( diff.extra, [] )
    
  def test_docdiff2( self ):
    docA = { "hello": {"mamba":["ricky","slowdance"]}, "below" : 49, "spanner" : 0, "bingo": {"mamba":{"ricky":"slowdance"}} }
    docB = { "hello": {"mamba": {"ricky":"speedskate"}}, "below" : 49, "spanner" : [], "bingo": {"mamba": {"ricky":"speedskate"}} }
    diff = docio.get_doc_diff( docA, docB )
    self.assertEqual( diff.equal, ['below'] )
    self.assertEqual( set(diff.unequal), set(['hello.mamba','spanner','bingo.mamba.ricky']))
    self.assertEqual( diff.missing, [] )
    self.assertEqual( diff.extra, [] )
    
  def test_docdiff3( self ):
    docA = { "hello": {"mamba":["ricky","slowdance"]}, "below" : 49, "spanner" : 0, "sideshow": 7, 'stimpy' : "bubble"  }
    docB = { "hello": {"mamba": {"ricky":"speedskate"}}, "below" : 49, "spanner" : [], "bingo": {"mamba": {"ricky":"speedskate"}} }
    diff = docio.get_doc_diff( docA, docB )
    self.assertEqual( diff.equal, ['below'] )
    self.assertEqual( set(diff.unequal), set(['hello.mamba','spanner']))
    self.assertEqual( diff.missing, ['bingo'] )
    self.assertEqual( set(diff.extra), set(['sideshow','stimpy']) )
    
  def test_docdiff4( self ):
    docA = { "list" : [ 0, 7, 2, 5 ] }
    docB = { "list" : [ 7, 2, 5 ] }
    diff = docio.get_doc_diff( docA, docB )
    self.assertEqual( diff.equal, [] )
    self.assertEqual( set(diff.unequal), set(['list.0','list.1','list.2']))
    self.assertEqual( diff.missing, [] )
    self.assertEqual( set(diff.extra), set(['list.3']) )
    
  def test_docdiff5( self ):
    docA = { "list" : [ "0", "7", "2", "5" ] }
    docB = { "list" : [ "0", "7", "2", "3" ] }
    diff = docio.get_doc_diff( docA, docB )
    self.assertEqual( diff.unequal, ['list.3'] )
    self.assertEqual( set(diff.equal), set(['list.0','list.1','list.2']))
    self.assertEqual( diff.missing, [] )
    self.assertEqual( diff.extra, [] )

