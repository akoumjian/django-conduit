from django.core.management.commands.runserver import Command as BaseCommand
from django.conf.urls import patterns, url, include
from conduit.api.utils import AutoAPI
from django.conf import settings
from importlib import import_module

class Command(BaseCommand):
    def get_handler(self, *args, **options):
        """
        Override the default urlconf to include our AutoAPI urls
        """
        urlconf_module = import_module(settings.ROOT_URLCONF)
        api = AutoAPI()
        urlconf_module.urlpatterns += patterns('', url(r'^api/', include(api.urls)))
        settings.ROOT_URLCONF = urlconf_module
        handler = super(Command, self).get_handler(*args, **options)
        return handler
