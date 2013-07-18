from django.db.models.loading import load_app, get_app, get_apps, get_models
from django.conf import settings

from conduit.api import ModelResource
from conduit.api import Api
from conduit.api.fields import ForeignKeyField, ManyToManyField


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

    def _get_related_fields_by_name(self, model):
        related_fields = {}

        opts = getattr(model, '_meta', None)
        if opts:
            for f in opts.get_all_field_names():
                field, model, direct, m2m = opts.get_field_by_name(f)
                name = field.name
                if direct and field.rel:
                    related_fields[field.name] = field
        return related_fields

    def _gen_resource(self, model):

        class AutoModelResource(ModelResource):
            class Meta(ModelResource.Meta):
                pass

            class Fields:
                pass

        AutoModelResource.Meta.model = model

        return AutoModelResource

    def _add_related(self, resource_instance):
        model = resource_instance.Meta.model
        related_fields = self._get_related_fields_by_name(model)

        # Iterate through related fields
        for name, field in related_fields.items():
            related_model = field.related.parent_model
            # If a resource already exists on the api with this model
            # use that resource
            related_resource_instance = self.api._by_model.get(related_model, [None])[0]

            if related_resource_instance:
                related_resource = related_resource_instance.__class__
            # Otherwise we create a new resource and attach it to the api
            else:
                related_resource = self._gen_resource(model)
                related_resource_instance = related_resource()
                self.api.register(related_resource_instance)

            # Update our parent resource instance to use related fields
            if hasattr(field.rel, 'through'):
                setattr(resource_instance.Fields, name, ManyToManyField(attribute=name, resource_cls=related_resource))
            else:
                setattr(resource_instance.Fields, name, ForeignKeyField(attribute=name, resource_cls=related_resource))

        return resource_instance

    def register_model(self, model):
        resource = self._gen_resource(model)
        resource_instance = resource()
        self.api.register(resource_instance)
        resource_instance = self._add_related(resource_instance)

    def register_app(self, app):
        for model in get_models(app):
            self.register_model(model)

    @property
    def urls(self):
        return self.api.urls
