from conduit.api import ModelResource
from conduit.exceptions import HttpInterrupt
from example.models import Foo
from conduit.whatever.testcases import ConduitTestCase


class MethodTestCase(ConduitTestCase):

    def setUp(self):
        class TestResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = Foo
        self.resource = TestResource()

    def test_allowed_methods(self):
        # Limit allowed methods to get and put
        self.resource.Meta.allowed_methods = ['get', 'put']

        get = self.factory.get('/foo/')
        put = self.factory.put('/foo/', {})
        post = self.factory.post('/foo/', {})
        delete = self.factory.delete('/foo')

        self.assertRaises(HttpInterrupt, self.resource.Meta.allowed_methods, [post, [], {}])
        self.assertRaises(HttpInterrupt, self.resource.Meta.allowed_methods, [delete, [], {}])
