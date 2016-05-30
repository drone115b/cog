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


def getClassPort( qt ):
    
    class Port( qt.QtGui.QGraphicsPathItem )  :
        
        NamePort = 1
        TypePort = 2
        MultiPort = 4 # input capable of multiple connections
        
        Type = qt.QtGui.QGraphicsItem.UserType + 128 + 1
        
        def __init__( self, parent=None, scene=None ):
            qt.QtGui.QGraphicsPathItem.__init__( self, parent, scene )
            self.label = qt.QtGui.QGraphicsTextItem( self )
            self.label.setDefaultTextColor(qt.QtGui.QColor.fromRgb(46,46,46))
            
            self.radius_ = 5
            self.margin = 2
            
            self.isMulti_ = False
            p = qt.QtGui.QPainterPath()
            p.addRoundedRect( -self.radius_, -self.radius_, self.radius_ << 1, self.radius_ << 1, 2, 2)
            self.setPath( p )
            
            self.setPen( qt.QtGui.QPen( qt.QtGui.QColor.fromRgb(100,100,100) )) 
            self.setBrush( qt.QtGui.QColor.fromRgb(100,100,100) )
            
            self.setFlag( qt.QtGui.QGraphicsItem.ItemSendsScenePositionChanges )
            
            self.m_portFlags = 0
            self.m_block = None
            self.name = None
            self.isOutput_ = False
            self.m_connections = []
            
            
            
        def del_(self):
            self.disconnect()

            
        def type( self ) :
            return self.Type 
            
        def setBlock( self, b ):
            self.m_block = b
            
        def setName( self, n ):
            self.name = n
            self.label.setPlainText( n )
            
        def setIsOutput( self, o ):
            self.isOutput_ = o
            fm = qt.QtGui.QFontMetrics( self.scene().font() )
            r = qt.QtCore.QRect( fm.boundingRect( self.name ) )
            
            if self.isOutput_ :
                self.label.setPos( -self.radius_ - self.margin - self.label.boundingRect().width(), -self.label.boundingRect().height() * 0.5 )
            else:
                self.label.setPos( self.radius_ + self.margin, -self.label.boundingRect().height() * 0.5 )
                
        def setIsMulti( self, m ):
            
            p = qt.QtGui.QPainterPath()
            if m :
                p.addEllipse(-self.radius_, -self.radius_, self.radius_ << 1, self.radius_ << 1)
            else :
                p.addRoundedRect( -self.radius_, -self.radius_, self.radius_ << 1, self.radius_ << 1, 2, 2)
            
            self.setPath( p )
            self.isMulti_ = m
            return
                
        def radius( self ) :
            return self.radius_
        
        def isOutput( self ):
            return self.isOutput_
        
        def isMulti( self ) :
            return self.isMulti_ or self.isOutput_ 
        
        def connections( self ):
            return self.m_connections
        
        def removeConnection( self, p ):
            # this is not the best way to remove a connection; typically you'd call
            # the connection.del_() so that both connected ports are updated
            self.m_connections = [ c for c in self.m_connections if c != p ]
            
        def disconnect( self ) :
            for c in self.m_connections :
                c.del_()
                c.setParentItem( None )
                self.scene().removeItem( c )
            self.m_connections = []
        
        def setPortFlags( self, f ):
            self.m_portFlags = f
            
            if self.m_portFlags & self.TypePort :
                font = qt.QtGui.QFont( self.scene().font() )
                font.setItalic( True )
                self.label.setFont( font )
                self.setPath( qt.QtGui.QPainterPath () )
            elif self.m_portFlags & self.NamePort :
                font = qt.QtGui.QFont( self.scene().font() )
                font.setBold( True )
                self.label.setFont( font )
                self.setPath( qt.QtGui.QPainterPath () )
            return
        
	def portName(self):
            return self.name
        
	def portFlags(self):
            return self.m_portFlags;
        
        def block( self ) :
            return self.m_block
            
        def isConnected( self, other ):
            for conn in self.m_connections :
                if other in ( conn.port1(), conn.port2() ) :
                    return True
            return False
        
        def itemChange( self, change, value ):
            if change == qt.QtGui.QGraphicsPathItem.ItemScenePositionHasChanged :
                for conn in self.m_connections :
                    conn.updatePosFromPorts()
                    conn.updatePath()
            return value
            
        
        
        
    return Port
