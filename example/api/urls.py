## api/urls.py
from django.conf.urls import patterns, include, url
from conduit.api import Api
from api.views import (
    BarResource, 
    BazResource,
    ContentTypeResource,
    FooResource,
    ItemResource,
)


api = Api()
api.register(BarResource())
api.register(BazResource())
api.register(ContentTypeResource())
api.register(FooResource())
api.register(ItemResource())

urlpatterns = patterns('',
    url(r'^', include(api.urls))
)
