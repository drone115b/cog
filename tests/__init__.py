# import all files in the directory
# reference: http://stackoverflow.com/questions/1057431/loading-all-modules-in-a-folder-in-python
#
from os.path import dirname, basename, isfile, join
import glob
TESTPATH = dirname( __file__ )
__modules = glob.glob(join( TESTPATH, "test_*.py"))
__all__ = [ basename(f)[:-3] for f in __modules if isfile(f) ] 
