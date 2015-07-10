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

import pwd
import os

def compile_code( src, context="script" ):
  return compile( src, "<cog %s>" % context, "exec" )


def execute_code( compiled_obj, globals_dict ):
  uid = os.getuid()
  gid = os.getgid()
  if uid == 0 or gid == 0 :
      raise SystemError( "Permission Denied" )
  else:
      exec( compiled_obj, globals_dict )
