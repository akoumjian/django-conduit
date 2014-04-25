from django.conf.urls import patterns, url, include
from conduit.api import ModelResource, Api
import example
import json
import example.urls
from example.models import Bar
from conduit.test.testcases import ConduitTestCase
from conduit.test.conduit_formats import ConduitBaseMixin
import uuid

class ResourceFormatTestCase(ConduitTestCase):
    urls = 'example.urls'

    def setUp(self):
        super(ResourceFormatTestCase, self).setUp()

        #
        #  create a resource as just functions
        #
        class TestResourceAsFunc(ModelResource):
            class Meta(ModelResource.Meta):
                conduit=(
                    'conduit.test.conduit_formats.build_pub',
                    'conduit.test.conduit_formats.return_response',
                )
                model = Bar
                pk_field = 'id'
        self.resource_as_func = TestResourceAsFunc()
        self.resource_as_func.Meta.api = Api(name="v1")
        self.resource_as_func.Meta.api.register(TestResourceAsFunc())

        #
        #  create a resource as a mixin class ( w/ explit paths )
        #
        class TestResourceAsMixin(ModelResource, ConduitBaseMixin):
            class Meta(ModelResource.Meta):
                conduit=(
                    'conduit.test.conduit_formats.ConduitBaseMixin.build_pub',
                    'conduit.test.conduit_formats.ConduitBaseMixin.return_response',
                )
                model = Bar
                pk_field = 'id'
        self.resource_as_mixin = TestResourceAsMixin()
        self.resource_as_mixin.Meta.api = Api(name="v1")
        self.resource_as_mixin.Meta.api.register(TestResourceAsMixin())

        #
        #  create a recommended resource ( no super class )
        #
        class TestResourceAsContext(ModelResource):
            class Meta(ModelResource.Meta):
                conduit=(
                    'conduit.test.conduit_formats.ConduitBaseMixin.build_pub',
                    'conduit.test.conduit_formats.ConduitBaseMixin.return_response',
                )
                model = Bar
                pk_field = 'id'
        self.resource_as_context = TestResourceAsContext()
        self.resource_as_context.Meta.api = Api(name="v1")
        self.resource_as_context.Meta.api.register(TestResourceAsContext())

        # override urls
        self.original_urls = example.urls.urlpatterns
        example.urls.urlpatterns += patterns(
            '',
            url(r'^api_as_func/', include(self.resource_as_func.Meta.api.urls)),
            url(r'^api_as_mixin/', include(self.resource_as_mixin.Meta.api.urls)),
            url(r'^api_as_context/', include(self.resource_as_context.Meta.api.urls))
        )

    def tearDown(self):
        super(ResourceFormatTestCase, self).tearDown()
        example.urls.urlpatterns = self.original_urls

    def test_resource_as_function(self):
        bar = Bar( name=str( uuid.uuid4() )[:8] )  
        bar.save()
        get_detail = self.factory.get('/{0}/{0}/'.format(bar.__class__.__name__,bar.id))
        response = self.resource_as_func.view( get_detail, *[], **{} )
        self.assertEqual(response['success'], True)

    def test_resource_as_mixin(self):
        bar = Bar( name=str( uuid.uuid4() )[:8] )  
        bar.save()
        get_detail = self.factory.get('/{0}/{0}/'.format(bar.__class__.__name__,bar.id))
        response = self.resource_as_mixin.view( get_detail, *[], **{} )
        self.assertEqual(response['success'], True)

    def test_resource_as_context(self):
        bar = Bar( name=str( uuid.uuid4() )[:8] )  
        bar.save()
        get_detail = self.factory.get('/{0}/{0}/'.format(bar.__class__.__name__,bar.id))
        response = self.resource_as_context.view( get_detail, *[], **{} )
        self.assertEqual(response['success'], True)
