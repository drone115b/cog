#####################################################################
#
# Copyright 2015 SpinVFX, 2016 Mayur Patel 
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

import copy
import sys
import traceback
import collections

from . import docinfo
from . import docobject

from .. import uid

###########################################################

# basic document container types:
#     - dictionaries
#     - lists
#     - objects (specialization of dictionaries)
# we don't need to go crazy over the scalar types (int,float,bool,string,etc)

# =========================================================

def get_view_typename( d ):
    # allow for no-name objects
    assert docinfo.is_keyvalue( d )
    key_parts = list(d.keys())[0].split()
    len_parts = len(key_parts)
    assert len_parts == 2 or len_parts == 1
    if len_parts == 1 :
        return ( key_parts[0], None )
    return tuple( key_parts )

# =========================================================

def get_view_body( d ):
    return list(d.items())[0][1]

# =========================================================


def do_recognize_schema( d, typenames ):
    if docinfo.is_keyvalue( d ):
        try:
            type_name = get_view_typename( d )[0]
            if type_name in typenames :
                return True
        except:
            pass
          
    return False 



## =========================================================

def get_attribute( obj, attrpath ):
    attrlist = attrpath.split( '.' )
    if attrpath  : 
        
        p = obj
        
        while attrlist : 
            
            if docinfo.is_object( p ):
                p = get_view_body( p.view )
                
            elif docinfo.is_dict(p) or docinfo.is_keyvalue(p) :
                if not attrlist[0] in p:
                    break # while
                p =  p[attrlist[0]]
                attrlist = attrlist[1:]
            elif docinfo.is_object_list( p ):
                count = 0
                for x in p:
                    if x.cogname == attrlist[0] :
                        p = get_view_body( x.view )
                        attrlist = attrlist[1:]
                        count += 1
                        break # for
                if count != 1 :
                    break # while
            elif docinfo.is_keyvalue_list( p ):
                count = 0
                for x in p:
                    if attrlist[0] in x :
                        p = x[ attrlist[0] ]
                        attrlist = attrlist[1:]
                        count += 1
                        break # for
                if count != 1 :
                    break # while
            elif docinfo.is_list( p ):
                p = p[int(attrlist[0])]
                attrlist = attrlist[1:]
            else:
                
                break # while
                        
            if not attrlist :
                return p

    raise KeyError( "Key %s cannot be resolved (from %s)" % (attrlist[0], attrpath ))
    

# -----------------------------------------------------


def set_attribute( obj, attrpath, document, ccn ):
    attrlist = attrpath.split( '.' )
    p = obj 
    
    validate_list = []
    while attrlist :
        
        if len( attrlist) > 1 :

              if docinfo.is_object( p ):
                  validate_list.append( p )
                  p = get_view_body( p.view )
              elif docinfo.is_dict(p) or docinfo.is_keyvalue(p) :
                  if not attrlist[0] in p:
                      break # while
                  p =  p[attrlist[0]]
                  attrlist = attrlist[1:]
              elif docinfo.is_object_list( p ):
                  count = 0
                  for x in p:
                      if x.cogname == attrlist[0] :
                          validate_list.append( x )
                          p = get_view_body( x.view )
                          attrlist = attrlist[ 1 :]
                          count += 1
                          break # for
                          
                  if count != 1 :
                      break # while
              elif docinfo.is_keyvalue_list( p ):
                  count = 0
                  for x in p:
                      if attrlist[0] in x :
                          p = x[ attrlist[0] ]
                          attrlist = attrlist[1:]
                          count += 1
                          break # for
                  if count != 1 :
                      break # while
              elif docinfo.is_list( p ):
                  p = p[int(attrlist[0])]
                  attrlist = attrlist[1:]
              else:
                  break # while
                  
        else: 
            # we need to allow the set to occur, creating a new entry if necessary
            # and catch any errors only through validation; 
            # because optional arguments may not already exist.
            while docinfo.is_object( p ):
                validate_list.append( p )
                p = get_view_body( p.view )
            
            if docinfo.is_dict(p) or docinfo.is_keyvalue(p) :
                p[attrlist[0]] = ccn.get_validated_view( document ) # will install it into document store!
            elif docinfo.is_object_list( p ):
                count = 0
                for x in p:
                    if x.cogname == attrlist[0] :
                        validate_list.append( x )
                        x.view = ccn.get_validated_view( document ) # will install it into document store!
                        count += 1
                        break # for
                    
                if count != 1 :
                    break # while
                   
            elif docinfo.is_keyvalue_list( p ):
                count = 0
                for x in p:
                    if attrlist[0] in x :
                        x[ attrlist[0] ] = ccn.get_validated_view( document ) # will install it into document store!
                        count += 1
                        break # for
                        
                if count != 1 :
                    break # while
                    
            elif docinfo.is_list( p ):
                index = int(attrlist[0])
                if -1 == index :
                    p.append( ccn.get_validated_view( document ) ) # will install it into document store!
                else:
                    p[ int(attrlist[0]) ] = ccn.get_validated_view( document ) # will install it into document store!
            else:
                break # while
                
            while validate_list :
                 p = validate_list.pop()
                 ObjClass = docobject.get_class( p.cogtype )
                 ObjClass.validate( ccn, p.view )
                 p.update_model(ccn) # view has changed, push changes to model
                
            return
      

    raise KeyError( "Key %s cannot be resolved (from %s)" % (attrlist[0], attrpath ))
    

# -----------------------------------------------------

def get_doc_children( doc, use_model_fields=False ):
    if docinfo.is_object( doc ):
        if use_model_fields :
            return doc.get_model_fields()
        else:
            doc = docio.get_view_body( doc.view )

    if docinfo.is_object_list( doc ):
        return [ x.cogname for x in doc ]
    elif docinfo.is_keyvalue_list( doc ):
        return [ x.keys()[0] for x in doc ]
    elif docinfo.is_dict( doc ) :
        return list(doc.keys())
    elif docinfo.is_list( doc ):
        return list(range(len(doc)))
        
    return None


# -----------------------------------------------------

DocDiff = collections.namedtuple( "DocDiff", ('equal','unequal','extra','missing'))
def get_doc_diff( docA, docB ):
    "returns equal fields, unequal fields, fields in A but not B (extra), and fields in B but not A (missing)"
    queue = [None]
    ret = DocDiff( [], [], [], [] )
    concat_paths = lambda attrpath, keys : ['.'.join([attrpath, k]) if attrpath else k for k in keys]
    while queue:
        attrpath = queue.pop()
        
        if attrpath :
            attrA = get_attribute( docA, attrpath )
            attrB = get_attribute( docB, attrpath )
        else:
            attrpath = ''
            attrA = docA
            attrB = docB
            
        if not docinfo.are_equivalent_types( attrA, attrB ):
            ret.unequal.append( attrpath )
        else:
            keysA = get_doc_children( attrA )
            keysB = get_doc_children( attrB )
            
            if keysA is not None and keysB is not None:
                keysA = set( keysA )
                keysB = set( keysB )
                commonkeys = keysA.intersection( keysB )
                extrakeys = keysA.difference( keysB )
                missingkeys = keysB.difference( keysA )
                
                ret.extra.extend( concat_paths( attrpath, extrakeys ) )
                ret.missing.extend( concat_paths( attrpath, missingkeys ) )
                queue.extend( concat_paths( attrpath, commonkeys ) )
                
            elif keysA is None and keysB is None:
                if attrA == attrB :
                    ret.equal.append( attrpath )
                else:
                    ret.unequal.append( attrpath )
            else:
                ret.unequal.append( attrpath )
            
    return ret

# =========================================================



