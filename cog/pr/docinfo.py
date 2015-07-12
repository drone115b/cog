#####################################################################
#
# Copyright 2015 SpinVFX 
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

from . import docobject

# -----------------------------------------------------

def is_object( obj ):
    return isinstance( obj, docobject.DocObject )

# -----------------------------------------------------

def is_object_type( obj, typename ):
    return is_object( obj ) and typename == obj.cogtype


# -----------------------------------------------------


def is_dict( obj ):
    try:
        value = obj[ 'key' ]
    except KeyError:
        return True
    except:
        return False
    return True
    

# -----------------------------------------------------

def is_string( obj ):
    try: # safe for python 2.x and 3.x
        ret = isinstance(obj, basestring)
    except:
        ret = isinstance(obj, str)
    return ret
    
    
# -----------------------------------------------------

def is_keyvalue( obj ):
    return is_dict(obj) and 1==len(obj)

# -----------------------------------------------------

def is_list( obj ) :
    try:
        return iter(obj) is not None and not is_dict( obj ) and not is_string( obj )
    except:
        pass
    return False
    

# -----------------------------------------------------


def is_object_list( obj ) :
    return is_list(obj) and all( is_object(x) for x in obj )
  

# -----------------------------------------------------


def is_keyvalue_list( obj ):
    return is_list(obj) and all( is_keyvalue(x) for x in obj )


# =========================================================
