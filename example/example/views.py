from conduit.pipes import ModelResource
from example.models import Foo


class FooResource(ModelResource):
    class Meta:
        model = Foo
