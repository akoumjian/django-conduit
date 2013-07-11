from django.http import HttpResponse
from django.db.models.fields import FieldDoesNotExist
from django.db import models
from django.utils import simplejson
from django.conf.urls import url, patterns
from decimal import Decimal
from dateutil import parser

import logging
logger = logging.getLogger(__name__)

from conduit import Conduit
from conduit.subscribe import subscribe, avoid, match
from conduit.exceptions import HttpInterrupt


class Api(object):
    _resources = []

    def __init__(self, name='v1'):
        self.name = name

    def register(self, resource_instance):
        self._resources.append(resource_instance)
        resource_instance.Meta.api = self

    @property
    def api_url(self):
        url_bits = [self.name]
        return '/'.join(url_bits)

    @property
    def urls(self):
        url_patterns = []
        for resource in self._resources:
            url_patterns.extend(resource._get_url_patterns())
        # url_patterns = patterns('', *url_patterns)
        return url_patterns


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
            'hydrate_request_data',
            'pre_get_list',
            'auth_get_detail',
            'auth_get_list',
            'auth_put_detail',
            'auth_put_list',
            'auth_post_detail',
            'auth_post_list',
            'auth_delete_detail',
            'auth_delete_list',
            'form_validate',
            'get_detail',
            'get_list',
            'initialize_new_object',
            'save_fk_objs',
            'put_detail',
            'post_list',
            'save_m2m_objs',
            'delete_detail',
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
        # Allowed order_by strings
        allowed_ordering = []
        # Optional default ordering
        default_ordering = None

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
        # Collect and check filters coming in through request
        get_params = request.GET.copy()

        # Remove special filters
        order_by = get_params.get('order_by', self.Meta.default_ordering)
        get_params.pop('order_by', None)
        if order_by:
            if order_by not in self.Meta.allowed_ordering:
                message = '{0} is not a valid ordering'.format(order_by)
                response = HttpResponse(message, status=400, content_type='application/json')
            kwargs['order_by'] = order_by

        # Add default filters
        filters = {}
        filters.update(self.Meta.default_filters)

        # Update from request filters
        for key, value in get_params.items():
            if key not in self.Meta.allowed_filters:
                response = HttpResponse('{0} is not an allowed filter'.format(key), status=400, content_type='application/json')
                raise HttpInterrupt(response)
            else:
                filters[key] = value

        kwargs['filters'] = filters
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
        data_dicts = kwargs.get('request_data', [])
        if isinstance(data_dicts, dict):
            data_dicts = [data_dicts]

        for data in data_dicts:
            for fieldname in data.keys():
                try:
                    model_field = self.Meta.model._meta.get_field(fieldname)
                    data[fieldname] = self._from_basic_type(model_field, data[fieldname])
                except FieldDoesNotExist:
                    # We don't try to modify fields we don't know about
                    # or artificial fields like resource_uri
                    pass
        return request, args, kwargs

    @match(match=['get', 'list'])
    def pre_get_list(self, request, *args, **kwargs):
        cls = self.Meta.model
        total_instances = cls.objects.all()
        # apply ordering
        if 'order_by' in kwargs:
            total_instances = total_instances.order_by(kwargs['order_by'])

        # apply filtering
        filtered_instances = total_instances.filter(**kwargs['filters'])
        kwargs['objs'] = filtered_instances
        kwargs['total_count'] = total_instances.count()
        return (request, args, kwargs)

    # Authorization hooks
    # Also defines allowed methods!
    @match(match=['get', 'detail'])
    def auth_get_detail(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['get', 'list'])
    def auth_get_list(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['put', 'detail'])
    def auth_put_detail(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['put', 'detail'])
    def auth_post_list(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['delete', 'detail'])
    def auth_delete_detail(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['delete', 'list'])
    def auth_delete_list(self, request, *args, **kwargs):
        response = HttpResponse('', status=405, content_type='application/json')
        raise HttpInterrupt(response)

    @match(match=['post', 'detail'])
    def auth_post_detail(self, request, *args, **kwargs):
        response = HttpResponse('', status=405, content_type='application/json')
        raise HttpInterrupt(response)

    @match(match=['put', 'list'])
    def auth_put_list(self, request, *args, **kwargs):
        response = HttpResponse('', status=405, content_type='application/json')
        raise HttpInterrupt(response)

    @subscribe(sub=['post', 'put'])
    def form_validate(self, request, *args, **kwargs):
        form_class = getattr(self.Meta, 'form_class', None)
        request_data = kwargs.get('request_data', {})
        if form_class and request_data:
            objs = kwargs.get('objs', [])

            # Only send fields from request data that exist
            # on model
            data = request_data.copy()
            fieldnames = self.Meta.model._meta.get_all_field_names()
            for key, val in data.items():
                if key not in fieldnames:
                    del data[key]
            print data
            errors = []
            for obj in objs:
                form = self.Meta.form_class(data, instance=obj)
                if not form.is_valid():
                    errors.append(form.errors)
            if errors:
                if len(errors) < 2:
                    errors = errors[0]
                errors_message = simplejson.dumps(errors)
                response = HttpResponse(errors_message, status=400, content_type='application/json')
                raise HttpInterrupt(response)

        return (request, args, kwargs)

    @match(match=['get', 'detail'])
    def get_detail(self, request, *args, **kwargs):
        kwargs['status'] = 200
        return (request, args, kwargs)

    @match(match=['get', 'list'])
    def get_list(self, request, *args, **kwargs):
        filtered_instances = kwargs['objs']
        limit_instances = filtered_instances[:self.Meta.limit]
        kwargs['objs'] = limit_instances
        kwargs['meta'] = {
            'total': kwargs['total_count'],
            'limit': self.Meta.limit
        }
        kwargs['status'] = 200
        return (request, args, kwargs)

    @match(match=['post', 'list'])
    def initialize_new_object(self, request, *args, **kwargs):
        # Before we attached foreign key objects, we have to have
        # an initialized object
        instance = self.Meta.model()
        kwargs['objs'] = [instance]
        return request, args, kwargs

    @subscribe(sub=['post', 'put'])
    def save_fk_objs(self, request, *args, **kwargs):
        # ForeignKey objects must be created and attached to the parent obj
        # before saving the parent object, since the field may not be nullable
        fields = self._get_explicit_fields()
        for field in fields:
            if getattr(field, 'related', None) == 'fk':
                related_data = kwargs['request_data'][field.attribute]
                field.save_related(self, kwargs['objs'][0], related_data)
        return request, args, kwargs

    @match(match=['put', 'detail'])
    def put_detail(self, request, *args, **kwargs):
        instance = self._update_from_dict(kwargs['objs'][0], kwargs['request_data'])
        instance.save()
        kwargs['objs'] = [instance]
        kwargs['status'] = 201
        return (request, args, kwargs)

    @match(match=['post', 'list'])
    def post_list(self, request, *args, **kwargs):
        instance = kwargs['objs'][0]
        instance = self._update_from_dict(instance, kwargs['request_data'])
        instance.save()
        kwargs['objs'] = [instance]
        kwargs['status'] = 201
        return (request, args, kwargs)

    @subscribe(sub=['post', 'put'])
    def save_m2m_objs(self, request, *args, **kwargs):
        fields = self._get_explicit_fields()
        for field in fields:
            if getattr(field, 'related', None) == 'm2m':
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

        if 'detail' in kwargs['pub'] or 'post' in kwargs['pub']:
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
