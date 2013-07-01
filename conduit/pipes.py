from importlib import import_module
from django.http import HttpResponse
from django.utils import simplejson
from decimal import Decimal
from django.db import models
import logging
from dateutil import parser
from django.conf.urls import url, patterns
logger = logging.getLogger(__name__)

from conduit.subscribe import subscribe, avoid, match


class HttpInterrupt(Exception):
    """
    Raise when req/resp cycle should end early and serve response

    ie: If an authorization fails, we can stop the conduit
    and serve an error message
    """
    def __init__(self, response):
        self.response = response or HttpResponse('No content')


class Api(object):
    _resources = []


    def __init__(self, name='api', version='v1'):
        self.name = name
        self.version = version

    def register(self, resource_instance):
        self._resources.append(resource_instance)
        resource_instance.Meta.api = self

    @property
    def api_url(self):
        url_bits = [self.name]
        if self.version:
            url_bits.append(self.version)
        return '/'.join(url_bits)

    @property
    def urls(self):
        url_patterns = []
        for resource in self._resources:
            url_patterns.extend(resource._get_url_patterns())
        url_patterns = patterns('', *url_patterns)
        return url_patterns


class Conduit(object):
    """
    Runs a request through a conduit and returns a response
    """
    def _get_method(self, method_string):
        method = getattr(self.__class__, method_string, None)
        if not method:
            pieces = method_string.split('.')
            if len(pieces) < 2:
                raise Exception('No such method found: {0}'.format(method_string))
            module = '.'.join(pieces[:-2])
            (cls, method,) = (pieces[-2], pieces[-1])
            module = import_module(module)
            cls = getattr(module, cls)
            method = getattr(cls, method)
        return method

    @classmethod
    def as_view(cls):
        """
        Returns a function for processing request response cycle
        """

        def view(request, *args, **kwargs):
            """
            Process the request, return a response
            """
            self = cls()
            for method_string in self.Meta.conduit[:-1]:
                method = self._get_method(method_string)
                try:
                    (request, args, kwargs,) = method(self, request, *args, **kwargs)
                except HttpInterrupt as e:
                    return e.response

            response_method = self._get_method(self.Meta.conduit[-1])
            return response_method(self, request, *args, **kwargs)

        return view


class ModelResource(Conduit):
    """
    RESTful api resource
    """

    class Meta:
        conduit = (
            'build_pub',
            'get_object_from_kwargs',
            'process_filters',
            'json_to_python',
            'check_permissions',
            'hydrate_request_data',
            'get_detail',
            'get_list',
            'post_detail',
            'put_detail',
            'post_list',
            'save_related_objs',
            'put_list',
            'delete_detail',
            'delete_list',
            'objs_to_bundles',
            'dehydrate_explicit_fields',
            'add_resource_uri',
            'produce_response_data',
            'serialize_response_data',
            'response'
        )
        resource_name = None
        pk_field = 'id'
        limit = 20
        api = None
        # Publically accessible filters designated by
        # filter string
        allowed_filters = []
        # Filter keys and values that are always applied
        # to get list requests
        default_filters = {}

    def forbidden(self):
        response = HttpResponse('', status=403, content_type='application/json')
        raise HttpInterrupt(response)

    def _update_from_dict(self, instance, data):
        instance.__dict__.update(data)
        return instance

    def _get_explicit_fields(self):
        fields = []
        field_meta = getattr(self, 'Fields', None)
        if field_meta:
            for fieldname, field in field_meta.__dict__.items():
                if not fieldname.startswith('_'):
                    fields.append(field)
        return fields

    def _get_resource_name(self):
        resource_name = getattr(self, 'resource_name', None)
        # Guess name from model if not set
        if not resource_name:
            resource_name = self.Meta.model._meta.module_name
        return resource_name

    def _get_resource_uri(self, obj=None, data=None):
        resource_uri = []

        # Grab the api portion
        api = getattr(self.Meta, 'api', None)
        if api:
            resource_uri.append(api.api_url)

        # Get the resource portion
        resource_uri.append(self._get_resource_name())

        # Get the object portion
        if obj:
            pk = getattr(obj, self.Meta.pk_field, None)
        elif data:
            pk = data.get(self.Meta.pk_field, None)
        else:
            pk = None
        if pk:
            resource_uri.append(str(pk))

        resource_uri = '/'.join(resource_uri)
        return resource_uri

    def _get_url_patterns(self):
        resource_uri = self._get_resource_uri()
        api = getattr(self.Meta, 'api')
        patterns = []

        # Generate list view
        list_view_pattern = r'^{0}/$'.format(resource_uri)
        list_view_name = '{0}-{1}-list'.format(api.name, self._get_resource_name())
        list_view = url(list_view_pattern, self.as_view(), name=list_view_name)
        patterns.append(list_view)

        # Generate detail view
        detail_view_pattern = r'^{0}/(?P<{1}>\w+)/$'.format(resource_uri, self.Meta.pk_field)
        detail_view_name = '{0}-{1}-detail'.format(api.name, self._get_resource_name())
        detail_view = url(detail_view_pattern, self.as_view(), name=detail_view_name)
        patterns.append(detail_view)

        return patterns

    def build_pub(self, request, *args, **kwargs):
        """
        Builds a list of keywords relevant to this request
        """
        pub = []
        pub.append(request.method.lower())
        if kwargs.get(self.Meta.pk_field, None):
            pub.append('detail')
        else:
            pub.append('list')
        kwargs['pub'] = pub
        return (request, args, kwargs)

    @subscribe(sub=['detail'])
    def get_object_from_kwargs(self, request, *args, **kwargs):
        """
        Retrieve instance of model referenced by url kwargs
        """
        cls = self.Meta.model
        try:
            kwds = {
                self.Meta.pk_field: kwargs[self.Meta.pk_field]
            }
            instance = cls.objects.get(**kwds)
        except cls.DoesNotExist:
            response = HttpResponse('Object does not exist', status=404, content_type='application/json')
            raise HttpInterrupt(response)
        kwargs['objs'] = [instance]
        return (request, args, kwargs)

    @subscribe(sub=['get'])
    def process_filters(self, request, *args, **kwargs):
        filters = {}
        # Collect and check filters coming in through request
        get_params = request.GET.copy()
        for key, value in get_params.items():
            if key not in self.Meta.allowed_filters:
                response = HttpResponse('{0} is not an allowed filter'.format(key), status=400, content_type='application/json')
                raise HttpInterrupt(response)
            else:
                filters[key] = value

        # Add default filters
        filters.update(self.Meta.default_filters)
        kwargs['filters'] = filters
        return (request, args, kwargs)

    def check_permissions(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @subscribe(sub=['post', 'put'])
    def json_to_python(self, request, *args, **kwargs):
        if request.body:
            data = request.body
            kwargs['request_data'] = simplejson.loads(data)
        return (request, args, kwargs)

    def _from_basic_type(self, field, data):
        """
        Convert deserialized data types into Python types
        """
        if isinstance(field, models.AutoField):
            return data

        if isinstance(field, models.BooleanField):
            return data

        if isinstance(field, models.CharField):
            return data

        if isinstance(field, models.TextField):
            return data

        if isinstance(field, models.IntegerField):
            return int(data)

        if isinstance(field, models.FloatField):
            return float(data)

        if isinstance(field, models.FileField):
            return data

        if isinstance(field, models.ImageField):
            return data

        if isinstance(field, models.DateTimeField):
            return parser.parse(data)

        if isinstance(field, models.DateField):
            return parser.parse(data)

        if isinstance(field, models.DecimalField):
            return Decimal(data)

        if isinstance(field, models.ForeignKey):
            return data

        if isinstance(field, models.ManyToManyField):
            return data

        logger.info('Could not find field type match for {0}'.format(field))
        return None

    @subscribe(sub=['post', 'put'])
    def hydrate_request_data(self, request, *args, **kwargs):
        """
        Manipulate request data before updating objects
        """
        # If updating/creating single object, we get a dict
        # change it to a list so we can place inside loop
        data_dicts = kwargs['request_data']
        if not isinstance(data_dicts, list):
            data_dicts = [data_dicts]

        for data in data_dicts:
            for fieldname in data.keys():
                model_field = self.Meta.model._meta.get_field(fieldname)
                data[fieldname] = self._from_basic_type(model_field, data[fieldname])
        return request, args, kwargs

    @match(match=['get', 'detail'])
    def get_detail(self, request, *args, **kwargs):
        kwargs['status'] = 200
        return (request, args, kwargs)

    @match(match=['get', 'list'])
    def get_list(self, request, *args, **kwargs):
        cls = self.Meta.model
        total_instances = cls.objects.all()
        filtered_instances = total_instances.filter(**kwargs['filters'])
        limit_instances = filtered_instances[:self.Meta.limit]
        kwargs['objs'] = limit_instances
        kwargs['meta'] = {
            'total': total_instances.count(),
            'limit': self.Meta.limit
        }
        kwargs['status'] = 200
        return (request, args, kwargs)

    @match(match=['put', 'detail'])
    def put_detail(self, request, *args, **kwargs):
        instance = self._update_from_dict(kwargs['objs'][0], kwargs['request_data'])
        instance.save()
        kwargs['objs'] = [instance]
        kwargs['status'] = 201
        return (request, args, kwargs)

    @match(match=['post', 'list'])
    def post_list(self, request, *args, **kwargs):
        instance = self.Meta.model()
        instance = self._update_from_dict(instance, kwargs['request_data'])
        instance.save()
        kwargs['objs'] = [instance]
        kwargs['status'] = 201
        return (request, args, kwargs)

    @subscribe(sub=['post', 'put'])
    def save_related_objs(self, request, *args, **kwargs):
        fields = self._get_explicit_fields()
        for field in fields:
            if field.related:
                related_data = kwargs['request_data'][field.attribute]
                field.save_related(self, kwargs['objs'][0], related_data)
        return request, args, kwargs

    @match(match=['detail', 'delete'])
    def delete_detail(self, request, *args, **kwargs):
        instance = kwargs['objs'][0]
        del kwargs['objs']
        instance.delete()
        kwargs['response'] = ''
        kwargs['status'] = 204
        return (request, args, kwargs)

    @match(match=['put', 'list'])
    def put_list(self, request, *args, **kwargs):
        kwargs['status'] = 501
        return (request, args, kwargs)

    @match(match=['post', 'detail'])
    def post_detail(self, request, *args, **kwargs):
        kwargs['status'] = 501
        return (request, args, kwargs)

    @match(match=['delete', 'list'])
    def delete_list(self, request, *args, **kwargs):
        kwargs['status'] = 501
        return (request, args, kwargs)

    @avoid(avoid=['delete'])
    def objs_to_bundles(self, request, *args, **kwargs):
        """
        Returns list of objects bundled with python dict representations

        Part of the dehydration process
        """
        objs = kwargs.get('objs', [])
        bundles = []
        for obj in objs:
            obj_data = {}
            for field in obj._meta.fields:
                dehydrated_value = self._to_basic_type(obj, field)
                obj_data[field.name] = dehydrated_value

            bundles.append({
                'obj': obj,
                'data': obj_data
            })

        kwargs['bundles'] = bundles
        return (request, args, kwargs)

    @avoid(avoid=['delete'])
    def dehydrate_explicit_fields(self, request, *args, **kwargs):
        """
        Iterates through field attributes and runs their dehydrate method
        """
        fields = self._get_explicit_fields()
        for bundle in kwargs['bundles']:
            for field in fields:
                field.dehydrate(self, bundle)
        return request, args, kwargs

    @avoid(avoid=['delete'])
    def add_resource_uri(self, request, *args, **kwargs):
        for bundle in kwargs['bundles']:
            bundle['data']['resource_uri'] = self._get_resource_uri(obj=bundle['obj'])
        return request, args, kwargs

    def _to_basic_type(self, obj, field):
        """
        Convert complex data types into serializable types
        """
        if isinstance(field, models.AutoField):
            return field.value_from_object(obj)

        if isinstance(field, models.BooleanField):
            return field.value_from_object(obj)

        if isinstance(field, models.CharField):
            return field.value_from_object(obj)

        if isinstance(field, models.TextField):
            return field.value_from_object(obj)

        if isinstance(field, models.IntegerField):
            return field.value_from_object(obj)

        if isinstance(field, models.FloatField):
            return field.value_from_object(obj)

        if isinstance(field, models.FileField):
            return field.value_to_string(obj)

        if isinstance(field, models.ImageField):
            return field.value_to_string(obj)

        if isinstance(field, models.DateTimeField):
            return field.value_to_string(obj)

        if isinstance(field, models.DateField):
            return field.value_to_string(obj)

        if isinstance(field, models.DecimalField):
            return field.value_to_string(obj)

        if isinstance(field, models.ForeignKey):
            return field.value_from_object(obj)

        ## FIXME: this is dangerous and stupid
        if isinstance(field, models.ManyToManyField):
            return eval(field.value_to_string(obj))

        logger.info('Could not find field type match for {0}'.format(field))
        return None

    @avoid(avoid=['delete'])
    def produce_response_data(self, request, *args, **kwargs):
        data_dicts = []
        for bundle in kwargs['bundles']:
            data_dicts.append(bundle['data'])

        if 'detail' in kwargs['pub']:
            kwargs['response_data'] = data_dicts[0]
        else:
            kwargs['response_data'] = {
                'meta': kwargs['meta'],
                'objects': data_dicts
            }
        return (request, args, kwargs)

    def serialize_response_data(self, request, *args, **kwargs):
        response = kwargs.get('response_data', None)
        kwargs['serialized'] = simplejson.dumps(response)
        return (request, args, kwargs)

    def response(self, request, *args, **kwargs):
        return HttpResponse(kwargs['serialized'], status=kwargs['status'], content_type='application/json')
