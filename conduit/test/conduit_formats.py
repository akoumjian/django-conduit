import logging
logger = logging.getLogger(__file__)

from conduit.subscribe import subscribe, avoid, match
from example.models import Bar, Baz, Foo

#
#  create a resource conduit
#  as just module-level functions
#
def build_pub(self, request, *args, **kwargs):
    pub = []
    pub.append(request.method.lower())
    if kwargs.get(self.Meta.pk_field, None):
        pub.append('detail')
    else:
        pub.append('list')
    kwargs['pub'] = pub 
    return (request, args, kwargs)

@subscribe(sub=[
    'get',
    'post',
    'put',
    'delete',
    'head',
    'options',
    'trace'
])  
def return_response(self, request, *args, **kwargs):
    response_data = { 
        'success' : True ,
        'status' : '200' , 
    }   
    return response_data


#
#  create a resource conduit
#  as class methods
#
class ConduitBaseMixin(object):

    def build_pub(self, request, *args, **kwargs):
        """ 
        Builds a list of keywords relevant to this request
        """
        pub = []
        pub.append(request.method.lower())
        if kwargs.get(self.Meta.pk_field, None):
            pub.append('detail')
        else:
            pub.append('list')
        kwargs['pub'] = pub 
        return (request, args, kwargs)

    @subscribe(sub=[
        'get',
        'post',
        'put',
        'delete',
        'head',
        'options',
        'trace'
    ])  
    def return_response(self, request, *args, **kwargs):
        response_data = { 
            'success' : True ,
            'status' : '200' , 
        }   
        return response_data

