from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from example.views import FooResource

urlpatterns = patterns('',
    url(r'^foo/$', FooResource.as_view(), name='foo-resource-list'),
    url(r'^foo/(?P<id>\d+)/$', FooResource.as_view(), name='foo-resource-detail'),
    url(r'^admin/', include(admin.site.urls)),
)
