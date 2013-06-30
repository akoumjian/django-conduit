from conduit.pipes import ModelResource
from example.models import Foo, Bar, Baz
from conduit.fields import ForeignKeyField, ManyToManyField


class BarResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Bar


class BazResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Baz


class FooResource(ModelResource):
    class Fields:
        bar = ForeignKeyField(attribute='bar', resource_cls=BarResource)
        bazzes = ManyToManyField(attribute='bazzes', resource_cls=BazResource)

    class Meta(ModelResource.Meta):
        model = Foo
