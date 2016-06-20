import inspect, os

#
# icons are stored in a directory simbling to where this module is stored.
# the directory is ./resources/icons/grey
#
ICONPATH = os.path.join( os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))), "resources", "icons", "grey" )

def get_icon( qt, name ):
    filename = "{}.svg".format( name )
    return qt.QtGui.QIcon( os.path.join( ICONPATH, filename ) )

