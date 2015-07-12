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
from . import docinfo
from . import docio


class UiObject( docobject.DocObject ):
    _cogtype = 'ui'
    
    def __init__(self, ccn, cogname, view):
        super( UiObject, self ).__init__(ccn, cogname, view)    

    @staticmethod
    def validate( ccn, doc ):
        """Should throw an exception if the document is not properly-formed for the type in question
        otherwise should pass,  Remember this is looking at a view, which is a plain-old data structure"""
        msgs = []
        if docio.do_recognize_schema( doc, (UiObject._cogtype,) ) :
            objtype, objname = docio.get_view_typename( doc )
            view = docio.get_view_body( doc )

            if not docinfo.is_dict( view ):
                raise TypeError( "Expected ui object to have a dictionary for its value" )
            else:
                for k in view:
                    if '.' not in k :
                        raise TypeError( "Expected a key of the form [<type>].<name>, in %s, found %s" % (objname, k ))
                    
        else:
           msgs.append( "Don't recognize schema for ui :\n%s" % str(doc))

        if msgs:
            raise TypeError('\n'.join( msgs ))
        return
      
    def update_model( self, ccn ):
        view = docio.get_view_body( self.view )
        new_dict = {}
        for k in view:
            objtype, objname = k.split( '.', 1 )
            new_key = k
            if objtype :
                found_obj = ccn.get_obj( objtype, objname ) if ccn.has_obj( objtype, objname ) else None
                if found_obj :
                    new_key = (objtype, found_obj)
            new_dict[ new_key ] = view[k]
        self.model = new_dict

    def update_view( self, ccn ):
        view = docio.get_view_body( self.view )
        new_dict = {}
        for k in self.model:
            new_key = k
            if not docinfo.is_string( k ):
                assert( docinfo.is_list( k ) and len(k)==2 )
                new_key = '%s.%s' % (k[1].cogtype, k[1].cogname)
            new_dict[ new_key ] = self.model[k]
        view.clear()
        view.update( new_dict )
      
    def apply_changes( self, ccn ):
        "Should apply changes to the ccn according to its function."
        pass

    def make_dup( self, ccn, newname ):
        # Deep copy of this object, entered into ccn with the new name.
        # Doesn't make sense to duplicate the object (at least in the context of keeping them in a ccn)
        return None

    def as_docs( self, ccn ):
        self.update_view(ccn) # catches renames, etc that might have occurred
        return [dict(self.view.items())]
        
    @staticmethod
    def serialize_order():
        return (None,None)
