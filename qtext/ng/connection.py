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


def getClassConnection( qt ):
    
    class Connection ( qt.QtGui.QGraphicsPathItem ) :
        
        Type = qt.QtGui.QGraphicsItem.UserType + 128 + 2
        
        def __init__( self, graphicsitem=None, scene=None ):
            qt.QtGui.QGraphicsPathItem.__init__( self, graphicsitem, scene )
            self.setPen( qt.QtGui.QPen( qt.QtGui.QColor.fromRgb(100,100,100), 2 ) )
            self.setFlag( qt.QtGui.QGraphicsItem.ItemIsSelectable )
            self.setZValue( -1 )
            self.m_port1 = None
            self.m_port2 = None
            self.pos1 = None
            self.pos2 = None
            
        def del_( self ) :
            self.m_port1.removeConnection(self)
            self.m_port1 = None # avoid circular reference
            
            self.m_port2.removeConnection(self)
            self.m_port2 = None # avoid circular reference
                
        def type( self ):
            return self.Type
        
        def setPos1( self, p ) :
            self.pos1 = p
            
        def setPos2( self, p ) :
            self.pos2 = p
            
        def setPort1( self, p ):
            self.m_port1 = p
            
        def setPort2( self, p ):
            self.m_port2 = p
            
        def updatePosFromPorts( self ):
            assert self.m_port1
            assert self.m_port2
            self.pos1 = self.m_port1.scenePos()
            self.pos2 = self.m_port2.scenePos()
            
        
        def updatePath( self ):
            startPos = self.pos1
            endPos = self.pos2
            
            p = qt.QtGui.QPainterPath()
            p.moveTo( startPos )
            
            dx = endPos.x() - startPos.x()
            dy = endPos.y() - startPos.y()
            
            ctr1 = qt.QtCore.QPoint( startPos.x() + dx * 0.25, startPos.y() + dy * 0.1 )
            ctr2 = qt.QtCore.QPoint( startPos.x() + dx * 0.75, startPos.y() + dy * 0.9 )
            p.cubicTo( ctr1, ctr2, endPos )
            self.setPath( p )
            
        def paint(self, painter, option, widget):
            if self.isSelected() :
                painter.setPen( qt.QtGui.QPen( qt.QtGui.QColor.fromRgb(180,180,20), 2 ) )
            else:
                painter.setPen( qt.QtGui.QPen( qt.QtGui.QColor.fromRgb(100,100,100), 2 ) )
                
            painter.drawPath( self.path() )
            
            
        def port1( self ) :
            return self.m_port1 
        
        def port2 ( self ):
            return self.m_port2
        
        

    return Connection
