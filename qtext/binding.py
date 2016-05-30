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
# reference:
# https://raw.githubusercontent.com/epage/PythonUtils/master/util/qt_compat.py
#
# reference:
# http://qt-project.org/wiki/Differences_Between_PySide_and_PyQt
#
# App-specific binding can be applied, to create a generic QtContext
# object that would ideally be compatible with both PySide and PyQt.
#


import collections
QtContext = collections.namedtuple( "QtContext", ["Qt", "QtCore","QtGui", "Signal", "Slot", "Property", "import_module", "id"] )


def getPyQt4Context( ):
    "Get a Qt context for using PyQt4 inside of python."
    import sip  as sipModule
    import PyQt4 as PyQt4Module
    try:
        sipModule.setapi('QString', 2)
        sipModule.setapi('QVariant', 2)
    except:
        print( "qt : Cannot force PyQt4 to APIv2 mode, potential data conversion problems with QString and QVariant classes." )
    
    import_module = lambda moduleName : getattr( __import__(PyQt4Module.__name__, globals(), locals(), [moduleName], -1), moduleName)

    import_module("QtCore")
    import_module("QtGui")
    
    Signal = PyQt4Module.QtCore.pyqtSignal
    Slot = PyQt4Module.QtCore.pyqtSlot
    Property = PyQt4Module.QtCore.pyqtProperty

    return QtContext( PyQt4Module, PyQt4Module.QtCore, PyQt4Module.QtGui, Signal, Slot, Property, import_module, "PyQt4" )


def getPySideContext( ):
    "Get a Qt context for using PySide inside of python."
    import PySide as PySideModule

    import_module = lambda moduleName : getattr( __import__(PySideModule.__name__, globals(), locals(), [moduleName], -1), moduleName)
    
    import_module("QtCore")
    import_module("QtGui")

    Signal = PySideModule.QtCore.Signal
    Slot = PySideModule.QtCore.Slot
    Property = PySideModule.QtCore.Property

    return QtContext( PySideModule, PySideModule.QtCore, PySideModule.QtGui, Signal, Slot, Property, import_module, "PySide" )


def getContext() : 
    "Gets any Qt context that it can find."
    try:
        return getPySideContext()
    except:
        return getPyQtContext()


#
# utilities only really relevant to PyQt4 api v1, which everyone should be trying to deprecate...
#
def toPyObject( obj ):
    "Use this on QVariant objects if you can't force PyQt4 into APIv2 mode."
    return obj.toPyObject() if hasattr( obj, 'toPyObject' ) else obj
  
def toString( obj ):
    "Use this on QString objects if you can't force PyQt4 into APIv2 mode."
    return obj.toString() if hasattr( obj, 'toString' ) else obj
    
