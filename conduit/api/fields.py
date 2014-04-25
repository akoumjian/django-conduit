import six
from importlib import import_module
from django.core.urlresolvers import resolve

class APIField(object):
    pass


def import_class(resource_cls_str):
    # import resource class dynamically
    import_str = resource_cls_str.split('.')
    module_str = '.'.join(import_str[:-1])
    cls_str = import_str[-1]
    module = import_module(module_str)
    resource_cls = getattr(module, cls_str)
    return resource_cls


class ForeignKeyField(APIField):
    dehydrate_conduit = (
        'bundles_from_objs',
        'auth_get_detail',
        'auth_get_list',
        'auth_put_detail',
        'auth_put_list',
        'auth_post_detail',
        'auth_post_list',
        'auth_delete_detail',
        'auth_delete_list',
        'response_data_from_bundles',
        'dehydrate_explicit_fields',
        'add_resource_uri',
    )

    save_conduit = (
        'check_allowed_methods',
        'get_object_from_kwargs',
        'hydrate_request_data',
        'bundles_from_request_data',
        'auth_get_detail',
        'auth_get_list',
        'auth_put_detail',
        'auth_put_list',
        'auth_post_detail',
        'auth_post_list',
        'auth_delete_detail',
        'auth_delete_list',
        'form_validate',
        'save_fk_objs',
        'update_objs_from_data',
        'save_m2m_objs',
    )

    def __init__(self, attribute=None, resource_cls=None, embed=False):
        self.related = 'fk'
        self.attribute = attribute
        self.embed = embed
        self.resource_cls = resource_cls

    def setup_resource(self):
        """
        Lazy load importing resource cls
        """
        # If we don't do this, imports will fail when trying
        # to import resources in the same file as the related
        # Field instantiation
        # If we are passed the string rep of a resource
        # class in python dot notation, import it
        if isinstance(self.resource_cls, six.string_types):
            self.resource_cls = import_class(self.resource_cls)

    def dehydrate(self, request, parent_inst, bundle=None):
        """
        Dehydrates a related object by running methods on a related resource
        """
        self.setup_resource()
        # build our request, args, kwargs to simulate regular request
        args = []
        obj = getattr(bundle['obj'], self.attribute)
        kwargs = {'objs': [obj], 'pub': ['detail', 'get']}
        resource = self.resource_cls()
        resource.Meta.api = parent_inst.Meta.api

        ## Only run dehydrate if we are embedding the resource
        if self.embed:
            for methodname in self.dehydrate_conduit:
                bound_method = resource._get_method(methodname)
                (request, args, kwargs,) = bound_method(request, *args, **kwargs)
            # Grab the dehydrated data and place it on the parent's bundle
            related_bundle = kwargs['bundles'][0]
            bundle['response_data'][self.attribute] = related_bundle['response_data']
        ## By default we just include the resource uri
        else:
            resource_uri = resource._get_resource_uri(obj=obj)
            bundle['response_data'][self.attribute] = resource_uri
        return bundle

    def save_related(self, request, parent_inst, obj, rel_obj_data):
        """
        Save the related object from data provided
        """
        self.setup_resource()

        # Expecting a resource_uri, so grab the pk, etc.
        if not self.embed or isinstance(rel_obj_data, six.string_types):
            func, args, kwargs = resolve(rel_obj_data)
            kwargs['pub'] = ['get', 'detail']
            pk_field = self.resource_cls.Meta.pk_field
            related_obj = self.resource_cls.Meta.model.objects.get(
                **{pk_field: kwargs[pk_field]}
            )
            kwargs['bundles'] = [{'obj': related_obj}]

        else:
            args = []
            kwargs = {
                'request_data': rel_obj_data,
            }
            # Add field to kwargs as if we had hit detail url
            pk_field = self.resource_cls.Meta.pk_field
            if pk_field in rel_obj_data:
                # Updated an existing object
                kwargs[pk_field] = rel_obj_data[pk_field]
                kwargs['pub'] = ['put', 'detail']
            else:
                # Creating a new object
                kwargs['pub'] = ['post', 'list']

        resource = self.resource_cls()
        resource.Meta.api = parent_inst.Meta.api
        for methodname in self.save_conduit:
            bound_method = resource._get_method(methodname)
            (request, args, kwargs,) = bound_method(request, *args, **kwargs)

        # Now we have to update the FK reference on the original object
        # before saving
        related_obj = kwargs['bundles'][0]['obj']
        setattr(obj, self.attribute, related_obj)

        return related_obj


class ManyToManyField(APIField):
    dehydrate_conduit = (
        'bundles_from_objs',
        'auth_get_detail',
        'auth_get_list',
        'auth_put_detail',
        'auth_put_list',
        'auth_post_detail',
        'auth_post_list',
        'auth_delete_detail',
        'auth_delete_list',
        'response_data_from_bundles',
        'dehydrate_explicit_fields',
        'add_resource_uri',
    )

    save_conduit = (
        'check_allowed_methods',
        'get_object_from_kwargs',
        'bundles_from_objs',
        'hydrate_request_data',
        'bundles_from_request_data',
        'auth_get_detail',
        'auth_get_list',
        'auth_put_detail',
        'auth_put_list',
        'auth_post_detail',
        'auth_post_list',
        'auth_delete_detail',
        'auth_delete_list',
        'form_validate',
        'save_fk_objs',
        'update_objs_from_data',
        'save_m2m_objs',
    )

    def __init__(self, attribute=None, resource_cls=None, embed=False):
        self.related = 'm2m'
        self.attribute = attribute
        self.embed = embed
        self.resource_cls = resource_cls

    def setup_resource(self):
        """
        Lazy load importing resource cls
        """
        # If we don't do this, imports will fail when trying
        # to import resources in the same file as the related
        # Field instantiation
        # If we are passed the string rep of a resource
        # class in python dot notation, import it
        if isinstance(self.resource_cls, six.string_types):
            self.resource_cls = import_class(self.resource_cls)

    def dehydrate(self, request, parent_inst, bundle=None):
        """
        Dehydrates a related object by running methods on a related resource
        """
        self.setup_resource()
        # build our request, args, kwargs to simulate regular request
        args = []
        # Get all the existing related objects on the parent obj
        objs = getattr(bundle['obj'], self.attribute).all()
        kwargs = {'objs': objs, 'pub': ['list', 'get']}
        resource = self.resource_cls()
        resource.Meta.api = parent_inst.Meta.api

        if self.embed:
            for methodname in self.dehydrate_conduit:
                bound_method = resource._get_method(methodname)
                (request, args, kwargs,) = bound_method(request, *args, **kwargs)

            dehydrated_data = []
            for related_bundle in kwargs['bundles']:
                dehydrated_data.append(related_bundle['response_data'])
        else:
            dehydrated_data = []
            for obj in objs:
                resource_uri = resource._get_resource_uri(obj=obj)
                dehydrated_data.append(resource_uri)
        bundle['response_data'][self.attribute] = dehydrated_data
        return bundle

    def save_related(self, request, parent_inst, obj, rel_obj_data):
        """
        Save the related object from data provided
        """
        self.setup_resource()
        # For ManyToMany, rel_obj_data should be formatted
        # as list!
        related_bundles = []
        pk_field = self.resource_cls.Meta.pk_field
        for obj_data in rel_obj_data:
            # Expecting a resource_uri, so grab the pk, etc.
            if not self.embed or isinstance(rel_obj_data, six.string_types):
                func, args, kwargs = resolve(obj_data)
                kwargs['pub'] = ['get', 'detail']

            else:
                args = []
                kwargs = {
                    'request_data': obj_data,
                }
                # Add field to kwargs as if we had hit detail url
                if pk_field in obj_data:
                    # Updated an existing object
                    kwargs[pk_field] = obj_data[pk_field]
                    kwargs['pub'] = ['put', 'detail']
                else:
                    # Creating a new object
                    kwargs['pub'] = ['post', 'list']


            resource = self.resource_cls()
            resource.Meta.api = parent_inst.Meta.api
            for methodname in self.save_conduit:
                bound_method = resource._get_method(methodname)
                (request, args, kwargs) = bound_method(request, *args, **kwargs)
            # Grab the dehydrated data and place it on the parent's bundle
            related_bundles.append(kwargs['bundles'][0])

        # Now we remove any ManyToMany relationships if
        # the related obj was not specified in rel_obj_data
        # This is because the rel_obj_data represents the
        # entire value of that field.
        related_objs = []
        for bundle in related_bundles:
            related_objs.append(bundle['obj'])
        
        # The parent object must be persisted before
        # we can use related managers
        if not getattr(obj, pk_field, None):
            obj.save()
        related_manager = getattr(obj, self.attribute)
        for attached_obj in related_manager.all():
            if attached_obj not in related_objs:
                # Django m2m fields we can remove
                if hasattr(related_manager, 'remove'):
                    related_manager.remove(attached_obj)
                # Only way to remove a reverse ForeignKey
                # is to delete the object!
                else:
                    attached_obj.delete()


        # Now add any related objects that we created
        # Adding an existing relationship has no effect
        for related_obj in related_objs:
            related_manager.add(related_obj)

        return related_objs
