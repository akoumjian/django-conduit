

class APIField(object):
    pass


class ForeignKeyField(APIField):
    dehydrate_conduit = (
        'objs_to_bundles',
        'add_resource_uri',
    )

    save_conduit = (
        'get_object_from_kwargs',
        'check_permissions',
        'hydrate_request_data',
        'put_detail',
        'post_list',
        'save_related_objs',
    )

    def __init__(self, attribute=None, resource_cls=None):
        self.related = True
        self.attribute = attribute
        self.resource_cls = resource_cls

    def dehydrate(self, parent_inst, bundle=None):
        """
        Dehydrates a related object by running methods on a related resource
        """
        # build our request, args, kwargs to simulate regular request
        request = None
        args = []
        obj = getattr(bundle['obj'], self.attribute)
        kwargs = {'objs': [obj], 'pub': ['detail', 'get']}
        resource = self.resource_cls()
        # pass the resource instance the parent's api
        # to generate correct resource uri's
        resource.Meta.api = parent_inst.Meta.api
        for methodname in self.dehydrate_conduit:
            method = resource._get_method(methodname)
            (request, args, kwargs,) = method(resource, request, *args, **kwargs)
        # Grab the dehydrated data and place it on the parent's bundle
        related_bundle = kwargs['bundles'][0]
        bundle['data'][self.attribute] = related_bundle['data']
        return bundle

    def save_related(self, parent_inst, obj, rel_obj_data):
        """
        Save the related object from data provided
        """
        request = None
        args = []
        kwargs = {
            'request_data': rel_obj_data,
            'pub': []
        }
        # Add field to kwargs as if we had hit detail url
        pk_field = self.resource_cls.Meta.pk_field
        if pk_field in rel_obj_data:
            kwargs[pk_field] = rel_obj_data[pk_field]

        # Do some introspection to tell if we are updating or
        # creating
        if pk_field in kwargs:
            kwargs['pub'].extend(['put', 'detail'])
        else:
            kwargs['pub'].extend(['post', 'list'])

        resource = self.resource_cls()
        resource.Meta.api = parent_inst.Meta.api
        for methodname in self.save_conduit:
            method = resource._get_method(methodname)
            (request, args, kwargs,) = method(resource, request, *args, **kwargs)
        # Grab the dehydrated data and place it on the parent's bundle
        related_obj = kwargs['objs'][0]

        # Now we have to update the FK reference on the original object
        # save_related takes objs as list for uniformity with
        # related fields that update multiple objects
        setattr(obj, self.attribute, related_obj)
        obj.save()
        return related_obj


class ManyToManyField(APIField):
    dehydrate_conduit = (
        'objs_to_bundles',
        'add_resource_uri',
    )

    save_conduit = (
        'get_object_from_kwargs',
        'check_permissions',
        'hydrate_request_data',
        'put_detail',
        'post_list',
        'save_related_objs',
    )

    def __init__(self, attribute=None, resource_cls=None):
        self.related = True
        self.attribute = attribute
        self.resource_cls = resource_cls

    def dehydrate(self, parent_inst, bundle=None):
        """
        Dehydrates a related object by running methods on a related resource
        """
        # build our request, args, kwargs to simulate regular request
        request = None
        args = []
        objs = getattr(bundle['obj'], self.attribute).all()
        kwargs = {'objs': objs, 'pub': ['list', 'get']}
        resource = self.resource_cls()
        resource.Meta.api = parent_inst.Meta.api
        for methodname in self.dehydrate_conduit:
            method = resource._get_method(methodname)
            (request, args, kwargs,) = method(resource, request, *args, **kwargs)

        dehydrated_data = []
        for related_bundle in kwargs['bundles']:
            dehydrated_data.append(related_bundle['data'])
        bundle['data'][self.attribute] = dehydrated_data
        return bundle

    def save_related(self, parent_inst, obj, rel_obj_data):
        """
        Save the related object from data provided
        """
        # For ManyToMany, rel_obj_data should be formatted
        # as list!
        related_objs = []
        for obj_data in rel_obj_data:
            request = None
            args = []
            kwargs = {
                'request_data': obj_data,
                'pub': []
            }
            # Add field to kwargs as if we had hit detail url
            pk_field = self.resource_cls.Meta.pk_field
            if pk_field in obj_data:
                kwargs[pk_field] = obj_data[pk_field]

            # Do some introspection to tell if we are updating or
            # creating the current related object
            if pk_field in kwargs:
                kwargs['pub'].extend(['put', 'detail'])
            else:
                kwargs['pub'].extend(['post', 'list'])

            resource = self.resource_cls()
            resource.Meta.api = parent_inst.Meta.api
            print resource.Meta.api
            for methodname in self.save_conduit:
                method = resource._get_method(methodname)
                (request, args, kwargs,) = method(resource, request, *args, **kwargs)
            # Grab the dehydrated data and place it on the parent's bundle
            related_objs.append(kwargs['objs'][0])

        # Now we remove any ManyToMany relationships if
        # the related obj was not specified in rel_obj_data
        # This is because the rel_obj_data represents the
        # entire value of that field.
        related_manager = getattr(obj, self.attribute)
        for attached_obj in related_manager.all():
            if attached_obj not in related_objs:
                related_manager.remove(attached_obj)

        # Now add any related objects that we created
        # Adding an existing relationship has no effect
        for related_obj in related_objs:
            related_manager.add(related_obj)

        return related_objs
