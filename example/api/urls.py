## api/urls.py
from django.conf.urls import patterns, include, url
from conduit.api import Api
from api.views import BarResource, BazResource, FooResource, GeoBarResource, GeoBazResource, GeoFooResource


api = Api()
api.register(BarResource())
api.register(BazResource())
api.register(FooResource())

# register geomanager resources
api.register(GeoBarResource())
api.register(GeoBazResource())
api.register(GeoFooResource())

urlpatterns = patterns('',
    url(r'^', include(api.urls))
)
