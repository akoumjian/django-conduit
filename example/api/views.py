## api/views.py
from django.contrib.contenttypes.models import ContentType

from conduit.api import ModelResource
from conduit.api.fields import ForeignKeyField, ManyToManyField, GenericForeignKeyField

from example.models import Bar, Baz, Foo, Item

from geoexample.models import GeoBar, GeoBaz, GeoFoo


class BarResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Bar
        # allowed_methods = ['get', 'put']


class BazResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Baz


class ContentTypeResource(ModelResource):
    """
    A resource for Django's ContentType model.
    """
    class Meta(ModelResource.Meta):
        model = ContentType


class FooResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Foo
    class Fields:
        bar = ForeignKeyField(attribute='bar', resource_cls=BarResource, embed=True)
        bazzes = ManyToManyField(attribute='bazzes', resource_cls=BazResource, embed=True)


class ItemResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Item

    class Fields:
        content_object = GenericForeignKeyField(
            attribute='content_object',
            resource_map={
                'Bar': 'api.views.BarResource'
            },
            embed=True
        )
#
#
#  resources based on GeoManager(s)
#
#
class GeoBarResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = GeoBar
        # allowed_methods = ['get', 'put']


class GeoBazResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = GeoBaz


class GeoFooResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = GeoFoo
    class Fields:
        bar = ForeignKeyField(attribute='bar', resource_cls=GeoBarResource, embed=True)
        bazzes = ManyToManyField(attribute='bazzes', resource_cls=GeoBazResource, embed=True)
