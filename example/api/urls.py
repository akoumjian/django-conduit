## api/urls.py
from django.conf.urls import patterns, include, url
from conduit.api import Api
from api.views import BarResource, BazResource, FooResource


api = Api()
api.register(BarResource())
api.register(BazResource())
api.register(FooResource())

urlpatterns = patterns('',
    url(r'^', include(api.urls))
)
