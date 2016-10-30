## api/views.py
from django.contrib.contenttypes.models import ContentType

from conduit.api import ModelResource, fields
from conduit.api.fields import ForeignKeyField, ManyToManyField, GenericForeignKeyField
from example.models import Bar, Baz, Foo, Item


class CustomField(fields.APIField):
    def __init__(self, attribute=None):
        self.attribute = attribute

    def from_basic_type(self, data):
        return data

    def to_basic_type(self, obj, field):
        return field.value_from_object(obj)

    def dehydrate(self, request, parent_inst, bundle=None):
        return bundle


class BarResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Bar


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
        bar = ForeignKeyField(
            attribute='bar',
            resource_cls=BarResource,
            embed=True
        )
        bazzes = ManyToManyField(
            attribute='bazzes',
            resource_cls=BazResource,
            embed=True
        )
        custom_field = CustomField(attribute='custom_field')


class ItemResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Item

    class Fields:
        content_object = GenericForeignKeyField(
            attribute='content_object',
            resource_map={
                'Bar': 'api.views.BarResource',
                'Foo': 'api.views.FooResource',
            },
            embed=True
        )
