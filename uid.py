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


#
# would be nice to use something like uuid1, but
# it benefits us to have a uuid which can be sorted in time order
# and where the time is /easily/ recovered from the uuid itself.
#    
# a "uid" is a 64b integer.  It could overflow to 65b after year 2040.
# a "uid" is guaranteed to be unique on the machine that generated it.
# there is a small probability of two machines generating the same uid at the same time, but it's pretty rare.
#

import random
import datetime
import time
import threading


EPOCH_YEAR = 2015
__RANDOMBITS = 14


def pretty_print( uid ):
    s = '%x' % uid
    s = s[::-1]
    l = len(s)
    return ( '-'.join([s[x:x+5] for x in range(0, l, 5)]) )[::-1]


def unpretty_print( uid_string ):
    s = uid_string.replace( '-','' )
    return int( s, 16 )


__CREATE_LOCK = threading.RLock()
def create_uid( target_datetime = None ):
    __CREATE_LOCK.acquire()
    t = None
    try:
        n = target_datetime if target_datetime else datetime.datetime.now()
        time.sleep( ( 2.0 / 1000000.0 ) ) # more than one microsecond - this is more a theoretical safeguard than anything else
        t = n.microsecond + n.second * 1000000 
        t += n.minute * 1000000 * 60 
        t += n.hour * 1000000 * 60 * 60
        t += (n.day-1) * 1000000 * 60 * 60 * 24 
        t += (n.month-1) * 1000000 * 60 * 60 * 24 * 33 
        t += (n.year - EPOCH_YEAR) * 1000000 * 60 * 60 * 24 * 33 * 12
        t <<= __RANDOMBITS
        randombits = random.SystemRandom().randint( 0, (1 << __RANDOMBITS)-1) # for some reason, the range on this function is inclusive.
        t |= randombits
    finally:
        __CREATE_LOCK.release()
    return t



def get_datetime( cog_uid ):
    t = cog_uid >> __RANDOMBITS
    year = t // (1000000 * 60 * 60 * 24 * 33 * 12)
    year += EPOCH_YEAR
    t %= (1000000 * 60 * 60 * 24 * 33 * 12)
    month = t // (1000000 * 60 * 60 * 24 * 33)
    month += 1
    t %= (1000000 * 60 * 60 * 24 * 33)
    day = t // (1000000 * 60 * 60 * 24)
    day += 1
    t %= (1000000 * 60 * 60 * 24)
    hour = t // (1000000 * 60 * 60)
    t %= (1000000 * 60 * 60)
    minute = t // (1000000 * 60)
    t %= (1000000 * 60)
    second = t // 1000000
    micros = t % 1000000
    return datetime.datetime( year=year, month=month, day=day, hour=hour, minute=minute, second=second, microsecond=micros )

    
