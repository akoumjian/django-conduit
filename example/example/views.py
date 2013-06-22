from example.pipeline import ModelResource
from example.models import Foo


class FooResource(ModelResource):
    class Meta:
        model = Foo
