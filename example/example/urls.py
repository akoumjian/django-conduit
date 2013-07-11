from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from conduit.api import Api
from example.views import FooResource

api = Api()
api.register(FooResource())

urlpatterns = patterns('',
    url(r'^api/', include(api.urls)),
    url(r'^admin/', include(admin.site.urls)),
)
