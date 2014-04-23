import inspect
from django.db.models.loading import load_app, get_app, get_apps, get_models
from django.conf import settings

from conduit.api import ModelResource
from conduit.api import Api
from conduit.api.fields import ForeignKeyField, ManyToManyField


class SelfDescModelResource(ModelResource):
    """
    A ModelResource that can print itself

    Used in auto building api boilerplate
    """
    def __to_string__(self):
        buff = ''
        buff += '\nclass {0}Resource(ModelResource):'.format(self.Meta.model.__name__)
        buff += self.__meta_to_string__()
        buff += self.__fields_to_string__()
        return buff

    def __meta_to_string__(self):
        buff = ''
        buff += '\n    class Meta(ModelResource.Meta):'
        buff += '\n        model = {0}'.format(self.Meta.model.__name__)
        return buff

    def __fields_to_string__(self):
        attributes = inspect.getmembers(self.Fields)
        attributes = [a for a in attributes if not a[0].startswith('__')]
        # Don't return Field class if no related fields
        if not attributes:
            return ''
        fields = []
        field_template = "{0} = {1}(attribute='{2}', resource_cls={3}Resource)"
        for att in attributes:
            keyword = att[0]
            field_type = att[1].__class__.__name__
            field_att = att[1].attribute
            field_res_cls = att[1].resource_cls.Meta.model.__name__
            field_str = field_template.format(keyword, field_type, field_att, field_res_cls)
            fields.append(field_str)

        buff = ''
        buff += '\n    class Fields:'
        for field in fields:
            buff += '\n        {0}'.format(field)
        return buff

    class Meta(ModelResource.Meta):
        pass

    class Fields:
        pass




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

    def __to_string__(self):
        buff = ''
        buff += self.__resource_str__()
        buff += '\n\n\n'
        buff += self.__urlconf_str__()
        return buff

    def __urlconf_str__(self):
        buff = '## api/urls.py'

        buff += '\nfrom django.conf.urls import patterns, include, url'
        buff += '\nfrom conduit.api import Api'

        # Resource import string
        import_tmp = '\nfrom api.views import {0}'
        res_names = [res.Meta.model.__name__ + 'Resource' for res in self.api._resources]
        buff += import_tmp.format(', '.join(res_names))
        buff += '\n\n'
        # Api Register strings
        buff += "\napi = Api(name='v1')"
        for res_name in res_names:
            buff += '\napi.register({0}())'.format(res_name)

        # Urlpatterns
        buff += "\n\nurlpatterns = patterns('',"
        buff += "\n    url(r'^', include(api.urls))"
        buff += "\n)"
        buff += '\n'

        return buff

    def __resource_str__(self):
        resources_str = '## api/views.py'

        # Add improt strings
        resources_str += '\nfrom conduit.api import ModelResource'
        resources_str += '\nfrom conduit.api.fields import ForeignKeyField, ManyToManyField'

        for app_name, models in self.api._app_models.items():
            resources_str += '\nfrom {0} import {1}'.format(app_name, ', '.join(models))

        # Add resource class strings
        for res in self.api._resources:
            resources_str += '\n\n'
            resources_str += res.__to_string__()
        resources_str += '\n'
        return resources_str

    def _get_related_fields_by_name(self, model):
        related_fields = {}

        opts = getattr(model, '_meta', None)
        if opts:
            for f in opts.get_all_field_names():
                field, model, direct, m2m = opts.get_field_by_name(f)
                if direct and field.rel:
                    related_fields[field.name] = field
        return related_fields

    def _gen_resource(self, model):

        class AutoModelResource(SelfDescModelResource):
            class Meta(SelfDescModelResource.Meta):
                pass
            class Fields(SelfDescModelResource.Fields):
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
        app_models = get_models(app)

        # Save reference of model names from model module
        # Used in auto string generation
        app_models_names = [model.__name__ for model in app_models]
        self.api._app_models.update({app.__name__: app_models_names})
        for model in app_models:
            self.register_model(model)

    @property
    def urls(self):
        return self.api.urls
