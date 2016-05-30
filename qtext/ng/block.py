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

def getClassBlock( qt ):
    Port = port.getClassPort( qt )

    class Block ( qt.QtGui.QGraphicsPathItem ) :
        Type = qt.QtGui.QGraphicsItem.UserType + 128 + 3
        
        def __init__( self, parent, scene, fillcolor=(128,128,128) ):
            qt.QtGui.QGraphicsPathItem.__init__( self, parent, scene)
            
            p = qt.QtGui.QPainterPath()
            p.addRoundedRect( -50, -15, 100, 30, 5, 5)
            self.setPath( p )
            self.setPen( qt.QtGui.QPen( qt.QtGui.QColor.fromRgb(115,115,115) ) )
            self.setBrush( qt.QtGui.QColor.fromRgb(*fillcolor) )
            self.setFlag( qt.QtGui.QGraphicsItem.ItemIsMovable )
            self.setFlag( qt.QtGui.QGraphicsItem.ItemIsSelectable )
            
            self.horzMargin = 20
            self.vertMargin = 5
            self.width = self.horzMargin
            self.height = self.vertMargin
            self.fillcolor = fillcolor
            
            self.highlight = None
            
            
        def del_( self ) :
            for port_ in self.childItems() :
                if port_.type() == Port.Type :
                    port_.del_()
                    port_.setParentItem( None )
                    self.scene().removeItem( port_ )
                    
            if self.highlight :
                self.highlight.setParentItem( None )
                self.scene().removeItem( self.highlight )
                self.highlight = None

            # end for
            
        def type( self ):
            return self.Type
            
        def addPort( self, name, isOutput, flags=0 ) : 
            port = Port( self )
            port.setName( name )
            port.setIsOutput( isOutput )
            port.setBlock( self ) 
            port.setPortFlags( flags )
            
            if flags & Port.MultiPort or isOutput:
                port.setIsMulti( True )
            
            fm = qt.QtGui.QFontMetrics( self.scene().font() )
            w = fm.width( name )
            h = fm.height()
            self.width = max( self.width, w + self.horzMargin )
            self.height = self.height + h
            half_width = self.width >> 1
            half_height = self.height >> 1
            
            p = qt.QtGui.QPainterPath()
            p.addRoundedRect( -half_width, -half_height, self.width, self.height, 5, 5 )
            self.setPath( p )
            
            y = self.vertMargin + port.radius() - half_height
            for port_ in self.childItems() :
                if port_.type() != Port.Type :
                    continue
                
                if port_.isOutput() :
                    port_.setPos( port_.radius() + half_width, y )
                else:
                    port_.setPos( -port_.radius() - half_width, y )
            
                y += h
            # end for
            
            return port
        
        def addInputPort( self, name ):
            return self.addPort( name, False )
        
        def addOutputPort( self, name ):
            return self.addPort( name, True )
        
        def addInputPorts( self, names ):
            return [ self.addInputPort( n ) for n in names ]
        
        def addOutputPorts( self, names ):
            return [ self.addOutputPort( n ) for n in names ]
        
        def paint(self, painter, option, widget):
            if self.isSelected() :
                painter.setPen( qt.QtGui.QPen( qt.QtGui.QColor.fromRgb(128,128,128) ) )
                painter.setBrush( qt.QtGui.QColor.fromRgb(180,180,20) )
            else:
                painter.setPen( qt.QtGui.QPen( qt.QtGui.QColor.fromRgb(32,32,32) ) )
                painter.setBrush( qt.QtGui.QColor.fromRgb(* self.fillcolor) )
                
            painter.drawPath( self.path() )
            
        def clone( self ) :
            b = Block( None, self.scene() )
            for port_ in self.childItems() :
                if port_.type() == Port.Type :
                    b.addPort( port_.portName(), port_.isOutput(), port_.portFlags() )
            return b
        
        def ports( self ):
            return [ p for p in self.childItems() if p.type() == Port.Type ]

        def enableHighlight( self, rgb = (180,180,20)) :
            if not self.highlight :
                self.highlight = qt.QtGui.QGraphicsPathItem( self, None )
                p = qt.QtGui.QPainterPath()
                
                rect = self.boundingRect()
                radius = 20
                
                p.addEllipse( rect.x() + rect.width() - radius, rect.y() - radius, radius*2, radius*2)
                self.highlight.setPath( p )
                self.highlight.setPen( qt.QtGui.QPen( qt.QtGui.QColor.fromRgb( *rgb ), 1 ))
                
                self.highlight.setBrush( qt.QtGui.QBrush( qt.QtGui.QColor.fromRgb( *rgb ) ))
                
                self.highlight.setFlag( qt.QtGui.QGraphicsItem.ItemStacksBehindParent )
            
            
        def disableHighlight( self ):
            if self.highlight :
                self.highlight.setParentItem( None )
                self.scene().removeItem( self.highlight )
                self.highlight = None
            
        def isHighlightEnabled( self ):
            return not( self.highlight is None )
        
        def itemChange( self, change, value ) :
            return value
                
        
    return Block

