from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from conduit.api import Api
from example.views import FooResource, BarResource, BazResource
api = Api()
api.register(FooResource())
api.register(BarResource())
api.register(BazResource())

## Experimental AutoAPI to quickly expose your projects resources
# from conduit.api.utils import AutoAPI
# api = AutoAPI('example')

urlpatterns = patterns('',
    url(r'^api/', include(api.urls)),
    url(r'^admin/', include(admin.site.urls)),
)
