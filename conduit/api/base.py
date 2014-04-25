import json
import six
from django.http import HttpResponse
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models.fields import FieldDoesNotExist
from django.db import models
from django.conf.urls import url
from decimal import Decimal
from dateutil import parser

import logging
logger = logging.getLogger(__name__)

from conduit import Conduit
from conduit.subscribe import subscribe, avoid, match
from conduit.exceptions import HttpInterrupt


class Api(object):
    _resources = []
    # Reference attached resources by model type
    _by_model = {}
    # List model names by app models module
    _app_models = {}

    def __init__(self, name='v1'):
        self.name = name

    def register(self, resource_instance):
        # Add to list of resources
        self._resources.append(resource_instance)
        # Add to dict of resources by model name
        model = getattr(resource_instance.Meta, 'model', None)
        if model:
            model_resources = self._by_model.get(model, [])
            model_resources.append(resource_instance)
            self._by_model[model] = model_resources

        # Attach the api to the resource instance
        resource_instance.Meta.api = self

    @property
    def api_url(self):
        url_bits = [self.name]
        return '/'.join(url_bits)

    @property
    def urls(self):
        url_patterns = []
        for resource in self._resources:
            url_patterns.extend(resource.urls)
        return url_patterns


class Resource(Conduit):
    """
    RESTful api resource
    """
    class Meta:
        resource_name = None
        pk_field = 'id'
        api = None

        # Default number of objects to return on
        # get list requests
        default_limit = 20
        max_limit = 200

        # List of allowed methods on a resource for simple
        # authorization limits
        allowed_methods = ['get', 'post', 'put', 'delete']
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

    def _get_resource_name(self):
        resource_name = getattr(self.Meta, 'resource_name', None)
        # Guess name from model if not set
        if not resource_name:
            resource_name = self.Meta.model._meta.module_name
        return resource_name

    def _get_resource_uri(self, obj=None, data=None):
        list_view_name, detail_view_name = self._get_view_names()

        try:
            if obj:
                resource_uri = reverse(detail_view_name, kwargs={self.Meta.pk_field: getattr( obj, self.Meta.pk_field )})
            else:
                resource_uri = reverse(list_view_name)
        except NoReverseMatch:
            message = 'No reverse match found for view name "{0}". Resource instance may need reference to an Api instance if you are using one. e.g. resource_instance.Meta.api = Api(name="v1")'
            if obj:
                message = message.format(detail_view_name)
            else:
                message = message.format(list_view_name)
            raise Exception(message)
        return resource_uri

    def _get_view_names(self):
        resource_name = self._get_resource_name()
        list_view_name = '_'.join([resource_name, 'list'])
        detail_view_name = '_'.join([resource_name, 'detail'])
        api = getattr(self.Meta, 'api', None)
        if api:
            list_view_name = '_'.join([api.name, list_view_name])
            detail_view_name = '_'.join([api.name, detail_view_name])
        return list_view_name, detail_view_name

    def _get_url_patterns(self):
        # Fetch the names of the views
        # ie: v1_foo_list
        list_view_name, detail_view_name = self._get_view_names()

        # Create url patterns
        # ie detail: r'foo/(?P<pk>\w+)/$
        resource_pattern = []
        api = getattr(self.Meta, 'api', None)
        if api:
            resource_pattern.append(api.api_url)
        resource_pattern.append(self._get_resource_name())
        resource_pattern = '/'.join(resource_pattern)
        list_view_pattern = r'^{0}/$'.format(resource_pattern)
        detail_view_pattern = r'^{0}/(?P<{1}>\w+)/$'.format(resource_pattern, self.Meta.pk_field)

        # Form all the views
        list_view = url(list_view_pattern, self.view, name=list_view_name)
        detail_view = url(detail_view_pattern, self.view, name=detail_view_name)

        # Return list of patterns
        patterns = []
        patterns.append(list_view)
        patterns.append(detail_view)

        return patterns

    @property
    def urls(self):
        return self._get_url_patterns()

    def create_json_response(self, py_obj, status=200):
        content = json.dumps(py_obj)
        response = HttpResponse(content=content, status=status, content_type='application/json')
        return response

    def forbidden(self):
        response = HttpResponse('', status=403, content_type='application/json')
        raise HttpInterrupt(response)

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

    def check_allowed_methods(self, request, *args, **kwargs):
        allowed_methods = getattr(self.Meta, 'allowed_methods', ['get', 'put', 'post', 'delete'])
        for keyword in kwargs['pub']:
            if keyword in ['get', 'put', 'post', 'delete'] and keyword not in allowed_methods:
                message = {'__all__': '{0} Method Not Allowed'.format(keyword.upper())}
                response = self.create_json_response(py_obj=message, status=405)
                raise HttpInterrupt(response)
        return request, args, kwargs

class ModelResource(Resource):
    """
    RESTful api resource based on Django Model
    """
    class Meta(Resource.Meta):
        conduit = (
            'build_pub',
            'check_allowed_methods',
            'get_object_from_kwargs',
            'process_filters',
            'apply_filters',
            'bundles_from_objs',
            'json_to_python',
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
            'limit_get_list',
            'save_fk_objs',
            'update_objs_from_data',
            'save_m2m_objs',
            'get_detail',
            'get_list',
            'put_detail',
            'put_list',
            'post_list',
            'delete_detail',
            'response_data_from_bundles',
            'dehydrate_explicit_fields',
            'add_resource_uri',
            'produce_response_data',
            'return_response'
        )

    def _update_from_dict(self, instance, data):
        """
        Update all non-relational fields in place
        """
        instance.__dict__.update(data)
        return instance

    def _get_explicit_fields(self):
        fields = []
        field_meta = getattr(self, 'Fields', None)
        if field_meta:
            for fieldname, field in six.iteritems(field_meta.__dict__):
                if not fieldname.startswith('_'):
                    fields.append(field)
        return fields

    def _get_explicit_field_by_attribute(self, attribute=None):
        explicit_fields = self._get_explicit_fields()
        for field in explicit_fields:
            if field.attribute == attribute:
                return field
        return None

    def _get_explicit_field_by_type(self, related=None):
        fields = self._get_explicit_fields()
        field_attributes = []
        for field in fields:
            if getattr(field, 'related', None) == related:
                field_attributes.append(field.attribute)
        return field_attributes

    def _get_model_fields(self, obj=None):
        """
        Get all Django model fields on an obj
        """
        if not obj:
            obj = self.Meta.model
        field_names = obj._meta.get_all_field_names()
        real_fields = []
        for field_name in field_names:
            if hasattr(obj, field_name):
                real_fields.append(field_name)
        return real_fields

    def _get_type_fieldnames(self, obj=None, field_type=None):
        """
        Return all the fieldnames of a specific type
        """
        if not obj:
            obj = self.Meta.model
        fieldnames = self._get_model_fields()
        matched_fieldnames = []
        for fieldname in fieldnames:
            field_tuple = obj._meta.get_field_by_name(fieldname)
            if isinstance(field_tuple[0], field_type):
                matched_fieldnames.append(fieldname)
        return matched_fieldnames

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

    def check_allowed_methods(self, request, *args, **kwargs):
        allowed_methods = getattr(self.Meta, 'allowed_methods', ['get', 'put', 'post', 'delete'])
        for keyword in kwargs['pub']:
            if keyword in ['get', 'put', 'post', 'delete'] and keyword not in allowed_methods:
                message = {'__all__': '{0} Method Not Allowed'.format(keyword.upper())}
                response = self.create_json_response(py_obj=message, status=405)
                raise HttpInterrupt(response)
        return request, args, kwargs

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
            message = {'__all__': 'Object does not exist'}
            response = self.create_json_response(py_obj=message, status=404)
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
            if (order_by not in self.Meta.allowed_ordering) and (order_by != self.Meta.default_ordering):
                message = {'__all__': '{0} is not a valid ordering'.format(order_by)}
                response = self.create_json_response(py_obj=message, status=400)
                raise HttpInterrupt(response)
            kwargs['order_by'] = order_by

        limit = int(get_params.get('limit', self.Meta.default_limit))
        get_params.pop('limit', None)
        if limit:
            if (limit > self.Meta.max_limit):
                message = {'__all__': '{0} is higher than max limit of {1}'.format(limit, self.Meta.max_limit)}
                response = self.create_json_response(py_obj=message, status=400)
                raise HttpInterrupt(response)
            kwargs['limit'] = limit

        offset = int(get_params.get('offset', 0))
        get_params.pop('offset', None)
        kwargs['offset'] = offset

        # Add default filters
        filters = {}
        filters.update(self.Meta.default_filters)

        # Update from request filters
        for key, value in six.iteritems(get_params):
            if key not in self.Meta.allowed_filters:
                message = {'__all__': '{0} is not an allowed filter'.format(key)}
                response = self.create_json_response(py_obj=message, status=400)
                raise HttpInterrupt(response)
            else:
                filters[key] = value

        kwargs['filters'] = filters
        return (request, args, kwargs)

    @match(match=['get', 'list'])
    def apply_filters(self, request, *args, **kwargs):
        """
        run against filters before authorization checks

        Makes per object authorization checks faster by
        limiting the instances it must iterate through
        """
        cls = self.Meta.model
        total_instances = cls.objects.all()
        # apply ordering
        if 'order_by' in kwargs:
            total_instances = total_instances.order_by(kwargs['order_by'])

        filtered_instances = total_instances.filter(**kwargs['filters'])
        kwargs['objs'] = filtered_instances
        kwargs['total_count'] = filtered_instances.count()
        return (request, args, kwargs)

    @match(match=['get'])
    def bundles_from_objs(self, request, *args, **kwargs):
        bundles = []
        for obj in kwargs['objs']:
            bundle = {}
            bundle['obj'] = obj
            bundles.append(bundle)
        kwargs['bundles'] = bundles
        return request, args, kwargs

    @subscribe(sub=['post', 'put'])
    def json_to_python(self, request, *args, **kwargs):
        if request.body:
            data = request.body
            kwargs['request_data'] = json.loads(data.decode('UTF-8'))
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
            if data:
                return int(data)

        if isinstance(field, models.FloatField):
            return float(data)

        if isinstance(field, models.FileField):
            return data

        if isinstance(field, models.ImageField):
            return data

        if isinstance(field, models.DateTimeField):
            if isinstance(data, six.string_types):
                return parser.parse(data)
            else:
                return data

        if isinstance(field, models.DateField):
            if isinstance(data, six.string_types):
                return parser.parse(data)
            else:
                return data

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
        change basic types to python types ready for model fields

        For example, change datetime strings to datetimes
        Or decimal strings to decimals
        """
        # Place single object dict in list
        # We treat all requests as if they had multiple objects
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
        kwargs['request_data'] = data_dicts
        return request, args, kwargs

    @subscribe(sub=['post', 'put'])
    def bundles_from_request_data(self, request, *args, **kwargs):
        """
        Form pairings of request data and new or existing objects
        """
        bundles = []
        objs = []
        pk_field = getattr(self.Meta, 'pk_field', 'id')
        for data in kwargs['request_data']:
            data_dict = data.copy()
            if 'put' in kwargs['pub']:
                # Updating existing object, so fetch it
                try:
                    obj = self.Meta.model.objects.get(**{pk_field: data_dict[pk_field]})
                except self.Meta.model.DoesNotExist:
                    message = {'__all__': '{0} with key {1} does not exist'.format(self.Meta.model, data_dict[pk_field])}
                    response = self.create_json_response(py_obj=message, status=400)
                    raise HttpInterrupt(response)
                except KeyError:
                    message = {'__all__': 'Data set missing id or key'}         
                    response = self.create_json_response(py_obj=message, status=400)
                    raise HttpInterrupt(response)
            else:
                obj = self.Meta.model()
            bundle = {}
            bundle['request_data'] = data_dict
            bundle['obj'] = obj
            bundles.append(bundle)
            objs.append(obj)
        kwargs['bundles'] = bundles
        kwargs['objs'] = objs
        return request, args, kwargs

    # Authorization hooks
    @match(match=['get', 'detail'])
    def auth_get_detail(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['get', 'list'])
    def auth_get_list(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['put', 'detail'])
    def auth_put_detail(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['put', 'list'])
    def auth_put_list(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['post', 'list'])
    def auth_post_list(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['delete', 'detail'])
    def auth_delete_detail(self, request, *args, **kwargs):
        return (request, args, kwargs)

    @match(match=['delete', 'list'])
    def auth_delete_list(self, request, *args, **kwargs):
        response = self.create_json_response(py_obj='', status=405)
        raise HttpInterrupt(response)

    @match(match=['post', 'detail'])
    def auth_post_detail(self, request, *args, **kwargs):
        response = self.create_json_response(py_obj='', status=405)
        raise HttpInterrupt(response)


    @subscribe(sub=['post', 'put'])
    def form_validate(self, request, *args, **kwargs):
        form_class = getattr(self.Meta, 'form_class', None)
        if form_class:
            fieldnames = self._get_model_fields()

            for bundle in kwargs['bundles']:
                data_copy = bundle['request_data'].copy()

                # Remove extra fields before validating forms
                # Such as resource_uri
                for key in list(data_copy.keys()):
                    if key not in fieldnames:
                        del data_copy[key]

                if 'obj' in bundle:
                    form = self.Meta.form_class(data_copy, instance=bundle['obj'])
                else:
                    form = self.Meta.form_class(data_copy)

                if not form.is_valid():
                    response = self.create_json_response(py_obj=form.errors, status=400)
                    raise HttpInterrupt(response)

        return (request, args, kwargs)

    @match(match=['get', 'list'])
    def limit_get_list(self, request, *args, **kwargs):
        """
        Paginate results after authorization filters
        """
        start = kwargs['offset']
        end = kwargs['offset'] + kwargs['limit']
        kwargs['bundles'] = kwargs['bundles'][start:end]
        return request, args, kwargs

    @subscribe(sub=['post', 'put'])
    def save_fk_objs(self, request, *args, **kwargs):
        # ForeignKey objects must be created and attached to the parent obj
        # before saving the parent object, since the field may not be nullable
        for bundle in kwargs['bundles']:
            obj = bundle['obj']
            request_data = bundle['request_data']

            # Get all ForeignKey fields on the Model
            fk_fieldnames = self._get_type_fieldnames(obj, models.ForeignKey)
            # Get explicit FK fields which are not Model fields
            fk_fieldnames.extend(self._get_explicit_field_by_type('fk'))
            # Make sure names are unique
            fk_fieldnames = set(fk_fieldnames)
            for fieldname in fk_fieldnames:
                # Get the data to process
                related_data = request_data[fieldname]
        
                # If we are using a related resource field, use it
                conduit_field = self._get_explicit_field_by_attribute(fieldname)
                if conduit_field:
                    try:
                        conduit_field.save_related(request, self, obj, related_data)
                    except HttpInterrupt as e:
                        # Raise the error but specify it as occuring within
                        # the related field
                        error_dict = {fieldname: json.loads(e.response.content)}
                        response = self.create_json_response(py_obj=error_dict, status=e.response.status_code)
                        raise HttpInterrupt(response)

                # Otherwise we do it simply with primary keys
                else:
                    id_fieldname = '{0}_id'.format(fieldname)
                    setattr(obj, id_fieldname, related_data)

        return request, args, kwargs

    @subscribe(sub=['post', 'put'])
    def update_objs_from_data(self, request, *args, **kwargs):
        """
        Update the objects in place with processed request data
        """
        for bundle in kwargs['bundles']:
            obj = bundle['obj']
            self._update_from_dict(obj, bundle['request_data'])
            obj.save()
            # Refetch the object so that we can return an accurate
            # representation of the data that is being persisted 
            bundle['obj'] = self.Meta.model.objects.get(**{self.Meta.pk_field: getattr( obj, self.Meta.pk_field )})
        return request, args, kwargs

    @subscribe(sub=['post', 'put'])
    def save_m2m_objs(self, request, *args, **kwargs):
        ## Must be done after persisting parent objects
        for bundle in kwargs['bundles']:
            obj = bundle['obj']
            request_data = bundle['request_data']

            # Get all M2M fields on the Model
            m2m_fieldnames = self._get_type_fieldnames(obj, models.ManyToManyField)
            # Get explicit m2m fields which are not Model fields
            m2m_fieldnames.extend(self._get_explicit_field_by_type('m2m'))
            m2m_fieldnames = set(m2m_fieldnames)
            for fieldname in m2m_fieldnames:
                # Get the data to process
                related_data = request_data[fieldname]
        
                # If we are using a related resource field, use it
                conduit_field = self._get_explicit_field_by_attribute(fieldname)
                if conduit_field:
                    try:
                        conduit_field.save_related(request, self, obj, related_data)
                    except HttpInterrupt as e:
                        # Raise the error but specify it as occuring within
                        # the related field
                        error_dict = {fieldname: json.loads(e.response.content)}
                        response = self.create_json_response(py_obj=error_dict, status=e.response.status_code)
                        raise HttpInterrupt(response)

                # Otherwise we do it simply with primary keys
                else:
                    related_manager = getattr(obj, fieldname)
                    # Remove any pk's not included in related_data
                    for attached_pk in related_manager.all().values_list('pk', flat=True):
                        if attached_pk not in related_data:
                            related_manager.remove(attached_pk)

                    # Add all pk's included in related_data
                    for related_pk in related_data:
                        related_manager.add(related_pk)

        return request, args, kwargs

    @match(match=['get', 'detail'])
    def get_detail(self, request, *args, **kwargs):
        kwargs['status'] = 200
        return (request, args, kwargs)

    @match(match=['get', 'list'])
    def get_list(self, request, *args, **kwargs):
        kwargs['meta'] = {
            'total': kwargs['total_count'],
            'limit': kwargs['limit'],
            'offset': kwargs['offset'],
        }
        kwargs['status'] = 200
        return (request, args, kwargs)

    @match(match=['put', 'detail'])
    def put_detail(self, request, *args, **kwargs):
        kwargs['status'] = 201
        return (request, args, kwargs)

    @match(match=['put', 'list'])
    def put_list(self, request, *args, **kwargs):
        kwargs['status'] = 201
        kwargs['meta'] = {'limit': len(kwargs['bundles'])}
        return request, args, kwargs

    @match(match=['post', 'list'])
    def post_list(self, request, *args, **kwargs):
        kwargs['status'] = 201
        return (request, args, kwargs)

    @match(match=['detail', 'delete'])
    def delete_detail(self, request, *args, **kwargs):
        instance = kwargs['objs'][0]
        del kwargs['objs']
        instance.delete()
        kwargs['response'] = ''
        kwargs['status'] = 204
        return (request, args, kwargs)

    @avoid(avoid=['delete'])
    def response_data_from_bundles(self, request, *args, **kwargs):
        """
        Prepare the response data dict for each object in bundles
        """
        bundles = kwargs['bundles']
        for bundle in bundles:
            obj = bundle['obj']
            obj_data = {}
            for fieldname in self._get_model_fields(obj):
                field = obj._meta.get_field_by_name(fieldname)[0]
                
                dehydrated_value = self._to_basic_type(obj, field)
                obj_data[fieldname] = dehydrated_value

            # Update the bundle in place
            bundle['response_data'] = obj_data
        return (request, args, kwargs)

    @avoid(avoid=['delete'])
    def dehydrate_explicit_fields(self, request, *args, **kwargs):
        """
        Iterates through field attributes and runs their dehydrate method
        """
        fields = self._get_explicit_fields()
        for bundle in kwargs['bundles']:
            for field in fields:
                field.dehydrate(request, self, bundle)
        return request, args, kwargs

    @avoid(avoid=['delete'])
    def add_resource_uri(self, request, *args, **kwargs):
        """
        Add the resource uri to each bundles response data
        """
        for bundle in kwargs['bundles']:
            bundle['response_data']['resource_uri'] = self._get_resource_uri(obj=bundle['obj'])
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
            data_dicts.append(bundle['response_data'])

        if 'detail' in kwargs['pub']:
            kwargs['response_data'] = data_dicts[0]
        if 'get' in kwargs['pub'] and 'list' in kwargs['pub']:
            kwargs['response_data'] = {
                'meta': kwargs['meta'],
                'objects': data_dicts
            }
        elif len(data_dicts) == 1:
            kwargs['response_data'] = data_dicts[0]
        else:
            kwargs['response_data'] = data_dicts

        return (request, args, kwargs)

    def return_response(self, request, *args, **kwargs):
        response_data = kwargs.get('response_data', '')
        response = self.create_json_response(py_obj=response_data, status=kwargs['status'])
        return response
