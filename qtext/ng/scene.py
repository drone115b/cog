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
#
# reference: STANISLAW ADASZEWSKI, qnodeseditor source code (C++)
#

from . import port
from . import connection
from . import block

def getClassScene( qt ):

    # supports connection creation with click and drag
    # supports connection creation with click and click
    # supports deletion of connections and blocks with del and backspace
    # supports toggle of highlight with spacebar
    # supports selection with click-block (default qt behaviour)
    
    Port = port.getClassPort( qt )    
    Connection = connection.getClassConnection( qt )
    Block = block.getClassBlock( qt )
    
    
    class ConnectionHandler( qt.QtCore.QObject )  :
        def __init__( self, parent = None ) :
            qt.QtCore.QObject.__init__( self, parent )
            self.scene = None
            self.conn = None 
            
        def install( self, scene ):
            scene.installEventFilter( self ) # circular reference
            self.scene = scene
        
        def registerConnection( self, port, conn ):
            if not port.isMulti() :
                port.disconnect()
            port.connections().append( conn )
            
        def beginConnection( self, item, pos ) :
             # connection handling:
            self.conn = Connection( None, self.scene )
            self.conn.setPort1( item )
            self.conn.setPos1( item.scenePos() )
            self.conn.setPos2( pos )
            self.conn.updatePath()
            return
            

        def endConnection( self, item ):
            port1 = self.conn.port1()
            port2 = item
            if port1.block() != port2.block() and port1.isOutput() != port2.isOutput() and (not port1.isConnected(port2)):
                self.conn.setPos2( port2.scenePos() )
                self.conn.setPort2( port2 )
                self.conn.updatePath()
                self.registerConnection( port1, self.conn )
                self.registerConnection( port2, self.conn )
                self.scene.connectionCreated.emit( self.conn )
                self.conn = None 
                return True
            return False
            
        def abortConnection( self ):
            # remove the connection from memory
            self.conn.setParentItem( None ) # scene is the parent
            self.scene.removeItem( self.conn ) # delete from scene
            self.conn = None # remove last reference to connection
            return            

        def eventFilter( self, o, e ):
            me = e # me = qt.QtGui.QGraphicsSceneMouseEvent( e )
            if e.type() == qt.QtCore.QEvent.GraphicsSceneMousePress :
                
                if me.button() == qt.QtCore.Qt.LeftButton :
                    item = self.scene.ngItemAt( me.scenePos() )
                        
                    if item and item.type() == Port.Type and (not self.conn): 
                        self.beginConnection( item, me.scenePos() )
                        return True
                        
                    elif item and item.type() == Port.Type and self.conn :
                        # support click-port, click-port
                        if self.endConnection( item ) :
                            return True
                    
            elif e.type() == qt.QtCore.QEvent.GraphicsSceneMouseMove  :
                if self.conn : 
                    self.conn.setPos2( me.scenePos() )
                    self.conn.updatePath()
                    return True

            elif e.type() == qt.QtCore.QEvent.GraphicsSceneMouseRelease :
                # support click-and-drag port to port
                if self.conn and ( me.button() == qt.QtCore.Qt.LeftButton ) :
                    item = self.scene.ngItemAt( me.scenePos() )
                    if item and ( item.type() == Port.Type ):
                        if self.endConnection( item ) :
                            return True
                    else:
                        if self.conn : 
                            self.abortConnection()
                            return True
                        
                
            return qt.QtCore.QObject.eventFilter( self, o, e )

    
    
    class Scene( qt.QtGui.QGraphicsScene ):
        
        connectionCreated = qt.Signal( qt.QtGui.QGraphicsPathItem )
        connectionDeleted = qt.Signal( qt.QtGui.QGraphicsPathItem )
        
        blockCreated = qt.Signal( qt.QtGui.QGraphicsPathItem ) # will be a Block
        blockDeleted = qt.Signal( qt.QtGui.QGraphicsPathItem ) # will be a Block
        
        highlightEnabled = qt.Signal( qt.QtGui.QGraphicsPathItem )
        highlightDisabled = qt.Signal( qt.QtGui.QGraphicsPathItem )
        
        def __init__( self, parent=None ):
            qt.QtGui.QGraphicsScene.__init__( self, parent )
            
            self.setBackgroundBrush(qt.QtGui.QColor.fromRgb(46,46,46))
        
            self.connhandler = ConnectionHandler( self )
            self.connhandler.install( self ) # circular reference
            
        def ngItemAt( self, pos ):
            
            x = pos.toPoint().x()
            y = pos.toPoint().y() 
            
            items = self.items( x-1, y-1, 3, 3 )
            for item in items :
                if (item.type() > qt.QtGui.QGraphicsItem.UserType + 128) and (item.type() < qt.QtGui.QGraphicsItem.UserType + 128 + 4):
                    return item
            return None
        
        
        def keyReleaseEvent (self, e ):
            if e.key() in ( qt.QtCore.Qt.Key_Backspace, qt.QtCore.Qt.Key_Delete ) :
                
                # backspace and delete keys delete selected connections and blocks
                
                blocks = []
                connections = []
                
                # delete connections first, then blocks:
                
                for item in self.selectedItems() :
                    if item.type() == Block.Type :
                        blocks.append( item )
                    if item.type() == Connection.Type :
                        connections.append( item )
                        
                for item in connections:
                    self.connectionDeleted.emit( item )
                    item.del_()
                    item.setParentItem( None )
                    self.removeItem( item )
                    
                for item in blocks:
                    self.blockDeleted.emit( item )
                    item.del_()
                    item.setParentItem( None )
                    self.removeItem( item )
                    
            elif e.key() == qt.QtCore.Qt.Key_Space :
                
                # spacebar toggles highlight on selected block
                
                for item in self.selectedItems() :
                    if item.type() == Block.Type :
                        if item.isHighlightEnabled() :
                            item.disableHighlight()
                            self.highlightDisabled.emit( item )
                        else:
                            item.enableHighlight()
                            self.highlightEnabled.emit( item )
                            

            return
    

    return Scene

