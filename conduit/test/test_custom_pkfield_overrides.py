from django.conf.urls import patterns, url, include
from conduit.api import ModelResource, Api
import example
import example.urls
from example.models import Bar
from conduit.test.testcases import ConduitTestCase
import uuid


class UriTestCase(ConduitTestCase):
    urls = 'example.urls'

    def setUp(self):
        super(UriTestCase, self).setUp()

        # create resource
        class TestResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = Bar
                pk_field = 'name'
                resource_name = 'custom_pk'
        self.resource = TestResource()
        self.resource.Meta.api = Api(name="v1")
        self.resource.Meta.api.register(TestResource())

        # override urls
        self.original_urls = example.urls.urlpatterns
        example.urls.urlpatterns += patterns(
            '',
            url(r'^api/', include(self.resource.Meta.api.urls))
        )

    def tearDown(self):
        super(UriTestCase, self).tearDown()
        example.urls.urlpatterns = self.original_urls

    def test_get_resource_uri_pkfield_override(self):
        bar = Bar( name=str( uuid.uuid4() )[:8] )  
        bar.save()
        resource_uri = self.resource._get_resource_uri( obj=bar )
        self.assertEqual(resource_uri, '/api/{0}/custom_pk/{1}/'.format(self.resource.Meta.api.name, bar.name))

    def test_update_objs_from_data_pkfield_override(self):
        bar = Bar( name=str( uuid.uuid4() )[:8] )  
        bar.save()
        put_detail = self.factory.put('/custom_pk/{0}/'.format(bar.name), {})
        kwargs = { 
            'pub': ['put', 'detail'],
            'bundles': [
                {   
                    'obj': bar,
                    'request_data': {
                        'name': '{0}'.format(bar.name),
                        'resource_uri': '/api/v1/custom_pk/{0}'.format(bar.name),
                    }   
                }   
            ]   
        } 
        request, args, kwargs = self.resource.update_objs_from_data( put_detail, **kwargs )
        # if the above didn't raise an error on pkfield
        # lookup, then we are good, but assert name anyhow
        self.assertEqual(kwargs['bundles'][0]['obj'].name, '{0}'.format(bar.name))

