from django.http import HttpResponse
from conduit.api import ModelResource
from conduit.api.fields import ForeignKeyField, ManyToManyField
from conduit.subscribe import match
from conduit.exceptions import HttpInterrupt
from example.models import Foo, Bar, Baz
from example.forms import FooForm, BarForm


class BarResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Bar
        # allowed_methods = ['get']
        form_class = BarForm


class BazResource(ModelResource):
    class Meta(ModelResource.Meta):
        model = Baz
        # allowed_methods = ['get']


class FooResource(ModelResource):
    class Fields:
        bar = ForeignKeyField(attribute='bar', resource_cls=BarResource)
        bazzes = ManyToManyField(attribute='bazzes', resource_cls=BazResource)

    class Meta(ModelResource.Meta):
        model = Foo

        # Test allowed methods
        # allowed_methods = ['get']

        form_class = FooForm

        allowed_filters = [
            'created__gt',
        ]
        allowed_ordering = [
            'created',
            '-created',
        ]

        # Test default filters
        # default_filters = {
        #     'integer__gt': 11
        # }
