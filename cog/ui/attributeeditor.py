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

import cog.pr.docinfo

import collections
import json

def getClassAttributeEditor( qt ):

    from . import attributemodel
    from . import pythonhighlighter
    
    AttributeModel = attributemodel.getClassAttributeModel( qt )
    PythonHighlighter = pythonhighlighter.getClassPythonHighlighter( qt )
    
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
        setAttrSignal = qt.Signal( str, str ) # attrpath, newvalue_doc
    
        def __init__(self, parent=None ):
            super(AttributeEditor,self).__init__( parent )
            self.obj = None
            self.model = None
            self.editcontext = None
            
            self.treeview_obj = AttributeTreeView( self )
            self.treeview_obj.selChangeSignal.connect( self.cb_currentChanged )

            self.lineedit_attrpath = qt.QtGui.QLineEdit('')
            self.lineedit_attrpath.textEdited.connect( self.cb_typingAttrpath )
            self.lineedit_attrpath.editingFinished.connect( self.cb_finishAttrpath )

            self.textedit_obj = qt.QtGui.QTextEdit( self ) 
            self.highlighter = None
            
            self.button_commit = qt.QtGui.QPushButton( self )
            self.button_commit.setIcon( icon.get_icon( qt, "done" ) )
            self.button_commit.clicked.connect( self.cb_commit )

            self.button_clear = qt.QtGui.QPushButton( self )
            self.button_clear.setIcon( icon.get_icon( qt, "close" ) ) 
            self.button_clear.clicked.connect( self.cb_clear )
            
            self.layout = qt.QtGui.QGridLayout()
            self.layout.addWidget( self.treeview_obj,               0, 0, 2, 1 )
            self.layout.addWidget( self.lineedit_attrpath,          0, 1, 1, 2 )
            self.layout.addWidget( self.textedit_obj,               1, 1, 1, 2 )
            self.layout.addWidget( self.button_clear,               2, 1, 1, 1 )
            self.layout.addWidget( self.button_commit,              2, 2, 1, 1 )
            
            self.layout.setColumnStretch(0, 8)
            self.layout.setColumnStretch(1, 8)
            self.layout.setColumnStretch(2, 8)
            self.layout.setRowStretch(1, 16)
            
            self.setLayout( self.layout )
            self.setTabOrder( self.treeview_obj, self.lineedit_attrpath )
            self.setTabOrder( self.lineedit_attrpath, self.textedit_obj )
            self.setTabOrder( self.textedit_obj, self.button_commit )
            self.setTabOrder( self.button_commit, self.button_clear )
            
            
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
            
        def cb_typingAttrpath( self, text ) :
            self.textedit_obj.document().clear()
            self.editcontext = None
            
        def cb_finishAttrpath( self ):
            ccn = self.model.getCCN()
            attrpath = self.lineedit_attrpath.text()
            try:
                value =  ccn.get_attr( attrpath )
                doc = qt.QtGui.QTextDocument( self._toEditable(value) )
                doc = self._setDocDecorators( doc )
                self.textedit_obj.setDocument( doc )
            except :
                pass
            self.editcontext = attrpath
            
            
        def cb_currentChanged( self, items ):
        
            currindex = items.indexes()
            self.textedit_obj.document().clear()
            self.lineedit_attrpath.setText('')
            self.editcontext = None
            
            if currindex:
                assert 1 == len( currindex )
                currindex = currindex[0]

                enableedits = False
                if self.model :
                    value = self.model.data( currindex, qt.QtCore.Qt.EditRole )
                    attrpath = self.model.attrPath( currindex )
                    enableedits = True
                    doc = qt.QtGui.QTextDocument( self._toEditable( value ) )
                    doc = self._setDocDecorators( doc )
                    self.textedit_obj.setDocument( doc )
                    self.lineedit_attrpath.setText( attrpath )
                    self.editcontext = attrpath
                    
        def cb_commit( self ):
            if self.editcontext :
                doc = self.textedit_obj.toPlainText().encode('ascii') # should be valid json
                doc = self._fromEditable( doc ) # deserialize the data structure
                self.setAttrSignal.emit( self.editcontext, doc )  # @@ all the work should be done here!
                
                # @@ BEGIN DELETE
                self.model.getCCN().set_attr( self.editcontext, doc )
                # @@ probabably should emit a signal here to refresh the master, queue in undo, etc etc.
                self.setCogObject( self.model.getCCN(), self.obj.cogtype, self.obj.cogname ) # reload, potentially with new attributes
                # @@ END DELETE
                
                self.editcontext = None
            self.treeview_obj.clearSelection()

        
        def cb_clear( self ):
            self.treeview_obj.clearSelection()
        
        @staticmethod
        def _toEditable( doc ):
            text = json.dumps( doc, default=AttributeEditor._objToEditable, sort_keys=True, indent=2 )
            if cog.pr.docinfo.is_string( doc ) :
                CHARS = { '\\n' : '\n', '\\r':'\r', '\\f': '\f', '\\v':'\v' }
                if any( key in text for key in CHARS.keys() ):
                    for key in CHARS :
                        text = text.replace( key, CHARS[key] )
                    assert text.startswith( '"' ) and text.endswith( '"' )
                    text = '"""' + text[1:-1] + '"""'
            return text
        
        @staticmethod
        def _fromEditable( text ):
            s = text
            if s.startswith( '"""' ) and s.endswith( '"""' ) :
                s = '"' + s[3:-3] + '"' 
                CHARS = { '\n' : '\\n', '\r':'\\r', '\f': '\\f', '\v':'\\v' }
                for key in CHARS :
                    s = s.replace( key, CHARS[key] )
            return json.loads( s )
        
        
        @classmethod
        def _objToEditable( cls, obj ):
            if hasattr( obj, '_view' ) :
                return obj._view
            raise TypeError
            
        def _setDocDecorators( self, doc ):
            fixedfont = qt.QtGui.QFont("Monospace")
            doc.setDefaultFont( fixedfont )
            self.highlighter = PythonHighlighter(doc)
            return doc
        
        
    return AttributeEditor

