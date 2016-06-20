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

from . import icon

import collections

import yaml

def getClassAttributeEditor( qt ):

    from . import attributemodel
    from . import yamlhighlighter # @@ need python highlighter for "code" attributes
    # @@ don't necessarily need yaml highligher because all the values will be strings except for code and "Null" 
    
    AttributeModel = attributemodel.getClassAttributeModel( qt )
    YamlHighlighter = yamlhighlighter.getClassYamlHighlighter( qt )
    
    AttributeEditContext = collections.namedtuple( "AttributeEditContext", ['ccn','attrpath'] )
    
    class AttributeTreeView( qt.QtGui.QTreeView ):
        selChangeSignal = qt.Signal( qt.QtGui.QItemSelection )
                
        def __init__(self, parent=None ):
            super( AttributeTreeView,self).__init__(parent)
            return
            
        def selectionChanged( self, curr, prev ):
            super( AttributeTreeView, self ).selectionChanged( curr, prev )
            self.selChangeSignal.emit( curr )
            return
    
    class AttributeEditor( qt.QtGui.QWidget ):
    
        def __init__(self, parent=None ):
            super(AttributeEditor,self).__init__( parent )
            self.obj = None
            self.model = None
            self.editcontext = None
            
            self.treeview_obj = AttributeTreeView( self )
            self.treeview_obj.selChangeSignal.connect( self.cb_currentChanged )

            self.textedit_obj = qt.QtGui.QTextEdit( self ) 
            self.highlighter = YamlHighlighter( self.textedit_obj.document() ) # @@
            
            self.label_attrpath = qt.QtGui.QLabel('')
            
            self.button_commit = qt.QtGui.QPushButton( self )
            self.button_commit.setIcon( icon.get_icon( qt, "done" ) )
            self.button_commit.clicked.connect( self.cb_commit )
            
            self.button_clear = qt.QtGui.QPushButton( self )
            self.button_clear.setIcon( icon.get_icon( qt, "close" ) ) 
            self.button_clear.clicked.connect( self.cb_clear )
            
            self.layout = qt.QtGui.QGridLayout()
            self.layout.addWidget( self.treeview_obj,               0, 0, 2, 1 )
            self.layout.addWidget( self.label_attrpath,             0, 1, 1, 2 )
            self.layout.addWidget( self.textedit_obj,               1, 1, 1, 2 )
            self.layout.addWidget( self.button_clear,               2, 1, 1, 1 )
            self.layout.addWidget( self.button_commit,              2, 2, 1, 1 )
            
            self.layout.setColumnStretch(0, 16)
            self.layout.setColumnStretch(1, 8)
            self.layout.setColumnStretch(2, 8)
            self.layout.setRowStretch(1, 16)
            
            self.setLayout( self.layout )
            
            
        def setCogObject(self, ccn, objtype, objname ):
            self.obj = ccn.get_obj( objtype, objname )
            self.model = AttributeModel( ccn, objtype, objname )
            self.editcontext = None
            self.treeview_obj.setModel( self.model )
            self.treeview_obj.expandAll()
            

        def clearCogObject( self) :
            self.obj = None
            self.model = None
            self.editcontext = None
            self.treeview_obj.setModel( qt.QtGui.QAbstractItemModel() )
            
            
        def cb_currentChanged( self, items ):
        
            currindex = items.indexes()
            self.textedit_obj.document().clear()
            self.label_attrpath.setText('')
            self.editcontext = None
            
            if currindex:
                assert 1 == len( currindex )
                currindex = currindex[0]

                enableedits = False
                if self.model :
                    value = self.model.data( currindex, qt.QtCore.Qt.EditRole )
                    attrpath = self.model.attrPath( currindex )
                    if 0 == self.model.child_count( currindex ) :
                        value = value if value is not None else 'Null'
                        enableedits = True
                        doc = qt.QtGui.QTextDocument( value )
                        self.highlighter = YamlHighlighter(doc)
                        self.textedit_obj.setDocument( doc )
                        self.label_attrpath.setText( attrpath )
                        self.editcontext = AttributeEditContext( self.model.getCCN(), attrpath )
                if enableedits:
                    self.textedit_obj.setEnabled( True )
                    self.button_clear.setEnabled( True )
                    self.button_commit.setEnabled( True )
                else:
                    self.textedit_obj.setDisabled( True )
                    self.button_clear.setDisabled( True )
                    self.button_commit.setDisabled( True )
                    
        def cb_commit( self ):
            # @@ apply to UNDO queue
            # @@ apply to script stack
        
            if self.editcontext:
                doc = self.textedit_obj.toPlainText()
                if doc.strip() in ('Null','null','NULL'):
                    doc = None
                self.editcontext.ccn.set_attr( self.editcontext.attrpath, doc )
                self.treeview_obj.clearSelection()

        
        def cb_clear( self ):
            self.treeview_obj.clearSelection()
    
    return AttributeEditor
