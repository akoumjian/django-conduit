

class APIField(object):
    # def dehydrate(self, parent_obj=None, parent_data=None, attribute=None):
    pass


class ForeignKeyField(APIField):
    dehydrate_conduit = (
        'objs_to_bundles',
    )

    def __init__(self, attribute=None, resource_cls=None):
        self.attribute = attribute
        self.resource_cls = resource_cls

    def dehydrate(self, bundle=None):
        """
        Dehydrates a related object by running methods on a related resource
        """
        # build our request, args, kwargs to simulate regular request
        request = None
        args = []
        obj = getattr(bundle['obj'], self.attribute)
        kwargs = {'instance': obj, 'pub': ['detail', 'get']}
        resource = self.resource_cls()
        for methodname in self.dehydrate_conduit:
            print methodname
            method = resource._get_method(methodname)
            (request, args, kwargs,) = method(resource, request, *args, **kwargs)
        # Grab the dehydrated data and place it on the parent's bundle
        related_bundle = kwargs['bundles'][0]
        bundle['data'][self.attribute] = related_bundle['data']
        return bundle


class ManyToManyField(APIField):
    dehydrate_conduit = (
        'objs_to_bundles',
    )

    def __init__(self, attribute=None, resource_cls=None):
        self.attribute = attribute
        self.resource_cls = resource_cls

    def dehydrate(self, bundle=None):
        """
        Dehydrates a related object by running methods on a related resource
        """
        # build our request, args, kwargs to simulate regular request
        request = None
        args = []
        objs = getattr(bundle['obj'], self.attribute).all()
        print objs
        kwargs = {'objs': objs, 'pub': ['list', 'get']}
        resource = self.resource_cls()
        for methodname in self.dehydrate_conduit:
            print methodname
            method = resource._get_method(methodname)
            (request, args, kwargs,) = method(resource, request, *args, **kwargs)

        dehydrated_data = []
        for related_bundle in kwargs['bundles']:
            dehydrated_data.append(related_bundle['data'])
        bundle['data'][self.attribute] = dehydrated_data
        return bundle
