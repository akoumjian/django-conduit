## api/views.py
from conduit.api import ModelResource
from conduit.api.fields import ForeignKeyField, ManyToManyField
from geoexample.models import GeoBar, GeoBaz, GeoFoo


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
