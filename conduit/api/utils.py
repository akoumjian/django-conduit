from django.db.models.loading import load_app, get_app, get_apps, get_models
from django.conf import settings

from conduit.api import ModelResource
from conduit.api import Api


class AutoAPI(object):
    """
    Automatically create sample APIs from Django Apps or Models
    """

    def __init__(self, *app_names):
        """
        app_names: One or more fully qualified django app names

        ie: api = AutoAPI('django.contrib.auth', 'example')
        """
        self.api = Api()
        apps = []
        if app_names:
            for app in app_names:
                app = load_app(app)
                apps.append(app)
        else:
            # Add all the apps if none are specified
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
