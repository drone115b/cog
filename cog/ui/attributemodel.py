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

# implement a model for object attributes : so that an attribute tree can be
# constructed for each cog object.  This also means that leafs will have values
# and an editor can be constructed to edit these values.

import cog.pr.docinfo

class AttributeModelNode(object):
    def __init__ (self, ccn, attrpath=None, parent=None):
        self.attrpath = '' if not attrpath else attrpath
        self.children = None
        self.parent = parent
        self.ccn = ccn
        self.label = ''
        if parent:
            self.parent.add_child(self)
            
    def add_child(self, child):
        if self.children is None:
            self._instance_children()
        self.children.append(child)
        
    def _instance_children(self):
        if self.children is None:
            self.children = []
            
            childattrs = self.ccn.get_attr_children( self.attrpath )
            if childattrs :
                for c in sorted( childattrs ):
                    newpath = '{0}.{1}'.format( self.attrpath, c )
                    newnode = AttributeModelNode( self.ccn, newpath, self ) # adds to self.children[]

        return

    def get_child(self, index):
        if self.children is None:
            self._instance_children()
        return self.children[index]
        
    def child_count(self):
        if self.children is None:
            self._instance_children()
        return len(self.children)
        
    def my_index(self):
        ret = 0
        if self.parent is not None:
            assert self.parent.children is not None
            ret = self.parent.children.index(self)
        return ret
        
    def help_name(self):
        ret = ''
        try : 
            obj = self.ccn.get_attr( self.attrpath )
            ret = obj.model.widget_help
        except:
            pass
        return ret

    def display_name(self):
        ret = self.attrpath.split('.')[-1]
        try:
            obj = self.ccn.get_attr( self.attrpath )
            if cog.pr.docinfo.is_object( obj ):
                ret = "{} ({}.{})".format( ret, obj.cogtype, obj.cogname )
        except KeyError:
            pass

        return ret
        
            
            
def getClassAttributeModel( qt ):

    class AttributeModel( qt.QtCore.QAbstractItemModel ):
        def __init__( self, ccn, objtype, objname ):
            super(AttributeModel,self).__init__()
            self.name = '{0}.{1}'.format( objtype, objname)
            self.root = AttributeModelNode(ccn, self.name )
            self.ccn = ccn
            
            
        def index(self, row, column, parent=qt.QtCore.QModelIndex()) :
            ret = qt.QtCore.QModelIndex()
            
            if not parent.isValid():
                parent_node = self.root
            else:
                parent_node = parent.internalPointer()
                
            child_count = parent_node.child_count()
            if row >= 0 and row < child_count :
                child_node = parent_node.get_child(row)
                ret = self.createIndex(row, column, child_node)
                
            return ret
            
        def parent(self, index):
            ret = qt.QtCore.QModelIndex()
            if index.isValid() :
                child_node = index.internalPointer()
                parent_node = child_node.parent
                if parent_node is not self.root :
                    row = parent_node.my_index()
                    ret = self.createIndex(row,0,parent_node)
            
            return ret
            
        def rowCount(self, parent):
            ret = 0
            if parent.isValid() :
                node = parent.internalPointer()
            else:
                node = self.root
            
            ret = node.child_count()
            return ret
            
        def columnCount(self, parent=qt.QtCore.QModelIndex()):
            return 1

        def data(self, index, role):
            
            value = None
            if index.isValid() :
                node = index.internalPointer()

                if role == qt.QtCore.Qt.DisplayRole :
                    value = node.display_name()
                elif role == qt.QtCore.Qt.ToolTipRole :
                    value = node.help_name()
                elif role == qt.QtCore.Qt.EditRole :
                    value = self.ccn.get_attr( node.attrpath )
                                    
            return value
            
        def attrPath(self, index):
            node = index.internalPointer()
            return node.attrpath
        
        def child_count(self, index):
            node = index.internalPointer()
            return node.child_count()
        
        def getCCN( self ):
            return self.ccn
            
        def headerData(self, section, orientation, role):
            ret = None
            if role == qt.QtCore.Qt.DisplayRole and 0 == section:
                ret = self.name
            return ret
        
        def flags(self, index):
            return qt.QtCore.Qt.ItemIsEnabled | qt.QtCore.Qt.ItemIsSelectable

    return AttributeModel

