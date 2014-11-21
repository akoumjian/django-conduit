## api/views.py
from conduit.api import ModelResource
from conduit.api.fields import ForeignKeyField, ManyToManyField
from example.models import Bar, Baz, Foo

class BarResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Bar
        # allowed_methods = ['get', 'put']


class BazResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Baz


class FooResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Foo
    class Fields:
        bar = ForeignKeyField(attribute='bar', resource_cls=BarResource, embed=True)
        bazzes = ManyToManyField(attribute='bazzes', resource_cls=BazResource, embed=True)

