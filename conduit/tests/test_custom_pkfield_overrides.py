import datetime
import dateutil
from django.conf.urls import patterns, url, include
from conduit.api import ModelResource, Api
from conduit.api.fields import ForeignKeyField, ManyToManyField
from conduit.exceptions import HttpInterrupt
import example
import example.urls
from example.models import Bar, Foo, Baz
from conduit.tests.testcases import ConduitTestCase
import uuid
import sys


class UriTestCase(ConduitTestCase):
    urls = 'example.urls'

    def setUp(self):
        super(UriTestCase, self).setUp()

        # create resource
        class TestResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = Bar
                pk_field = 'name'
        self.resource = TestResource()
        self.resource.Meta.api = Api(name="v1")
        self.resource.Meta.api.register(TestResource())

        # override urls
        self.original_urls = example.urls.urlpatterns
        example.urls.urlpatterns = patterns(
            '',
            url(r'^api/', include(self.resource.Meta.api.urls))
        )

    def tearDown(self):
        super(UriTestCase, self).tearDown()
        example.urls.urlpatterns = self.original_urls

    def test_detail_uri_pkfield_override(self):
        bar = Bar( name=str( uuid.uuid4() )[:8] )  
        bar.save()
        resource_uri = self.resource._get_resource_uri( obj=bar )
        print >> sys.stdout, resource_uri
        self.assertEqual(resource_uri, '/api/{0}/bar/{1}/'.format(self.resource.Meta.api.name, bar.name))

