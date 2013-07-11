from django.db.models import get_app, get_apps, get_models
from django.conf import settings

from conduit.api import ModelResource
from conduit.api import Api

class AutoAPI(object):
    """
    Automatically create sample APIs from Django Apps or Models
    """

    def __init__(self, apps=None):
        self.api = Api()
        if not apps:
            # Add all the apps in settings if none are specified
            apps = get_apps()
        for app in apps:
            self.register_app(app)

    def _gen_resource(self, model):
        class AutoModelResource(ModelResource):
            class Meta(ModelResource.Meta):
                pass
        AutoModelResource.Meta.model = model
        return AutoModelResource

    def register_model(self, model):
        resource = self._gen_resource(model)
        self.api.register(resource())

    def register_app(self, app):
        for model in get_models(app):
            self.register_model(model)

    @property
    def urls(self):
        return self.api.urls
