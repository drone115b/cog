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

import os

#######################################
#
# CLIENT CONFIGURATION:
#

# general configurations must start with COG

__default = {}
# cog script path
__default['COG_SCRIPTPATH'] = os.environ.get( 'COG_SCRIPTPATH', '' )
__default['COG_AUTHPATH'] = os.environ.get( 'COG_AUTHPATH', None )
__default['COG_SERVERS'] = [s.strip() for s in os.environ.get( 'COG_SERVERS', "" ).split(',')]


#######################################
#
# SERVER CONFIGURATION:
#

# server-only configurations must start with COGSERVER

__default_server = __default.copy()
__default_server[ 'COGSERVER_CLEANUP_INTERVAL' ] = int(os.environ.get( 'COGSERVER_CLEANUP_INTERVAL', 60 * 60 * 12 )) # 12 hours
__default_server[ 'COGSERVER_ARCHIVE_INTERVAL' ] = int(os.environ.get( 'COGSERVER_ARCHIVE_INTERVAL', 60 * 60 * 24 * 7 * 3 )) # 3 weeks
__default_server[ 'COGSERVER_PERMISSIONS_EXPIRY' ] = int(os.environ.get( 'COGSERVER_PERMISSIONS_EXPIRY', 60 * 15 )) # 15 minutes
__default_server[ 'COGSERVER_DATABASE' ] = os.environ.get( 'COGSERVER_DATABASE', '/var/lib/cog/cog.db' )
__default_server[ 'COGSERVER_BACKUP_INTERVAL' ] = int(os.environ.get( 'COGSERVER_BACKUP_INTERVAL', 60 * 60 * 4 )) # 4 hours
__default_server[ 'COGSERVER_BACKUPPATH' ] = os.environ.get( 'COGSERVER_BACKUPPATH', '/var/lib/cog/backup/' )
__default_server[ 'COGSERVER_MAINTENANCE_INTERVAL' ] = int(os.environ.get( 'COGSERVER_MAINTENANCE_INTERVAL', 60 * 60 * 8 )) # 8 hours

#######################################
#

def get_default_config( ):
    return __default.copy()


def get_default_server_config():
    return __default_server.copy()