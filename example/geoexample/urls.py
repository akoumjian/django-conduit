## api/urls.py
from django.conf.urls import patterns, include, url
from conduit.api import Api
from api.views import (
    GeoBarResource,
    GeoBazResource,
    GeoFooResource
)


api = Api()

# register geomanager resources
api.register(GeoBarResource())
api.register(GeoBazResource())
api.register(GeoFooResource())

urlpatterns = patterns('',
    url(r'^', include(api.urls))
)
