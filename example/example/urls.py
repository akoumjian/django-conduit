from django.conf.urls import include, url


urlpatterns = [
    url(r'^api/', include('api.urls'))
]
