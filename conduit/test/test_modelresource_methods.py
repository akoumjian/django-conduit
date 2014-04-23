import datetime
import dateutil
from decimal import Decimal
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from conduit.api import ModelResource, Api
from conduit.api.fields import ForeignKeyField, ManyToManyField
from conduit.exceptions import HttpInterrupt
from example.models import Bar, Foo, Baz
from conduit.test.testcases import ConduitTestCase


class MethodTestCase(ConduitTestCase):

    def setUp(self):
        class TestResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = Bar
                default_filters = {
                    'name__gte': 'beta',
                    'name__lte': 'zeta'
                }
                allowed_filters = [
                    'name__lte',
                ]
                allowed_ordering = [
                    '-name',
                ]
        self.resource = TestResource()
        self.resource.Meta.api = Api(name='v1')

    def test_build_pub(self):
        detail_get = self.factory.get('/foo/1/')
        list_get = self.factory.get('/foo/')
        put_detail = self.factory.put('/foo/1/', {})

        pk_field = self.resource.Meta.pk_field
        request, args, kwargs = self.resource.build_pub(detail_get, **{pk_field: 1})
        self.assertIn('detail', kwargs['pub'])
        self.assertIn('get', kwargs['pub'])

        request, args, kwargs = self.resource.build_pub(list_get)
        self.assertIn('list', kwargs['pub'])
        self.assertIn('get', kwargs['pub'])

    def test_allowed_methods(self):
        # Limit allowed methods to get and put
        self.resource.Meta.allowed_methods = ['get', 'put']

        get = self.factory.get('/foo/')
        put = self.factory.put('/foo/', {})
        post = self.factory.post('/foo/', {})
        delete = self.factory.delete('/foo')

        request, args, kwargs = self.resource.build_pub(post, [], {})
        self.assertRaises(HttpInterrupt, self.resource.check_allowed_methods, post, *args, **kwargs)
        request, args, kwargs = self.resource.build_pub(delete, [], {})
        self.assertRaises(HttpInterrupt, self.resource.check_allowed_methods, delete, *args, **kwargs)
        try:
            request, args, kwargs = self.resource.build_pub(get, [], {})
            self.resource.check_allowed_methods(request, *args, **kwargs)
        except HttpInterrupt:
            self.fail('check_allowed_methods should not raise HttpInterrupt on valid method')
        try:
            request, args, kwargs = self.resource.build_pub(put, [], {})
            self.resource.check_allowed_methods(request, *args, **kwargs)
        except HttpInterrupt:
            self.fail('check_allowed_methods should not raise HttpInterrupt on valid method')

    def test_get_object_from_kwargs(self):
        instance = self.resource.Meta.model()
        instance.save()

        pk_field = self.resource.Meta.pk_field
        kwargs = {
            'pub': ['detail'],
            pk_field: instance.pk
        }

        request, args, kwargs = self.resource.get_object_from_kwargs(None, [], **kwargs)
        self.assertIn(instance, kwargs['objs'])

    def test_process_filters(self):
        list_get = self.factory.get('/foo/?name__lte=delta&order_by=-name')
        kwargs = {
            'pub': ['get']
        }
        request, args, kwargs = self.resource.process_filters(list_get, [], **kwargs)
        filters = kwargs['filters']
        self.assertEqual(filters.get('name__gte', None), 'beta', msg='Default filter was not included')
        self.assertEqual(filters.get('name__lte', None), 'delta', msg='Param filters should override default filters')
        self.assertEqual(kwargs.get('order_by', None), '-name', msg='Ordering was not added to kwargs')

    def test_invalid_filter(self):
        list_get = self.factory.get('/foo/?name__lt=delta')
        kwargs = {
            'pub': ['get']
        }
        self.assertRaises(
            HttpInterrupt,
            self.resource.process_filters,
            list_get, **kwargs
        )

    def test_invalid_order_by(self):
        list_get = self.factory.get('/foo/?order_by=name')
        kwargs = {
            'pub': ['get']
        }
        self.assertRaises(
            HttpInterrupt,
            self.resource.process_filters,
            list_get, **kwargs
        )

    def test_json_to_python(self):
        import json
        py_data = {
            'fieldname': 'fieldvalue',
        }
        data = json.dumps(py_data)
        detail_put = self.factory.put('/bar/1/', data, content_type='application/json')
        kwargs = {
            'pub': ['put']
        }
        request, args, kwargs = self.resource.json_to_python(detail_put, data, **kwargs)
        self.assertEqual(kwargs.get('request_data', None), py_data)

    def test_hydrate_request_data(self):
        self.resource.Meta.model = Foo
        post_hydrate_data = {
            'bar': {
                'name': 'New Bar',
            },
            'bazzes': [
                {
                    'name': 'New Baz'
                },
            ],
            'birthday': datetime.datetime(2013, 6, 19),
            'boolean': False,
            'created': datetime.datetime(2013, 6, 21, 1, 44, 57, 367956, tzinfo=dateutil.tz.tzutc()),
            'decimal': Decimal('110.12'),
            'file_field': 'test/test.txt',
            'float_field': 100000.123456789,
            'id': 1,
            'integer': 12,
            'name': 'Foo Name',
            'text': 'text goes here'
        }

        request_data = {
            'bar': {
                'name': 'New Bar',
            },
            'bazzes': [
                {
                    'name': 'New Baz',
                }
            ],
            'birthday': '2013-06-19',
            'boolean': False,
            'created': '2013-06-21T01:44:57.367956+00:00',
            'decimal': '110.12',
            'file_field': 'test/test.txt',
            'float_field': 100000.123456789,
            'id': 1,
            'integer': 12,
            'name': 'Foo Name',
            'text': 'text goes here'
        }
        kwargs = {
            'request_data': [request_data],
            'pub': ['post', 'list']
        }
        post_list = self.factory.post('/foo/')
        request, args, kwargs = self.resource.hydrate_request_data(post_list, **kwargs)
        self.assertEqual([post_hydrate_data], kwargs['request_data'])

    def test_form_validate(self):
        class BarForm(forms.ModelForm):
            class Meta:
                model = Bar

            def clean_name(self):
                data = self.cleaned_data['name']
                raise forms.ValidationError('Fake validation error', code='fake')
                return data
        self.resource.Meta.form_class = BarForm
        bar = Bar.objects.create()
        kwargs = {
            'pub': ['post', 'list'],
            'bundles': [
                {
                    'obj': bar,
                    'request_data': {
                        'name': 'whatevs',
                        'resource_uri': '/api/v1/bar/{0}'.format(bar.pk),
                        'random_field': 'foobar'
                    }
                }
            ]
        }

        post_list = self.factory.post('/bar/')

        self.assertRaises(HttpInterrupt, self.resource.form_validate, post_list, [], **kwargs)

    def test_get_detail(self):
        get_detail = self.factory.get('/foo/1/')
        kwargs = {
            'pub': ['get', 'detail']
        }
        request, args, kwargs = self.resource.get_detail(get_detail, [], **kwargs)
        self.assertEqual(kwargs['status'], 200)

    def test_save_fk_objs(self):
        class FooResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = Foo
            class Fields:
                bar = ForeignKeyField(attribute='bar', resource_cls=self.resource.__class__, embed=True)

        foo_resource = FooResource()
        foo = Foo(
            **{ 'name': 'zed',
                'text': '',
                'integer': 9,
                'float_field': 123.123,
                'boolean': True,
                'decimal': '12.34',
                'file_field': 'test.mov',
            }
        )
        foo.save()
        post_list = self.factory.post('/foo/')
        kwargs = {
            'pub': ['post', 'list'],
            'bundles': [{
                'request_data': {
                    'name': 'foo name',
                    'bar': {
                        'name': 'bar name'
                    },
                },
                'obj': foo
            }],
        }
        request, args, kwargs = foo_resource.save_fk_objs(post_list, [], **kwargs)
        self.assertEqual(kwargs['bundles'][0]['obj'].bar.name, 'bar name')

    def test_save_m2m_objs(self):
        class BazResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = Baz

        class FooResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = Foo
            class Fields:
                bazzes = ManyToManyField(attribute='bazzes', resource_cls=BazResource, embed=True)

        foo_resource = FooResource()
        foo = Foo(
            **{ 'name': 'zed',
                'text': '',
                'integer': 9,
                'float_field': 123.123,
                'boolean': True,
                'decimal': '12.34',
                'file_field': 'test.mov',
            }
        )
        foo.save()
        post_list = self.factory.post('/foo/')
        kwargs = {
            'pub': ['post', 'list'],
            'bundles': [{
                'request_data': {
                    'name': 'foo name',
                    'bazzes': [
                        {'name': 'baz 1'}, {'name': 'baz 2'}
                    ]
                },
                'obj': foo
            }]
        }
        request, args, kwargs = foo_resource.save_m2m_objs(post_list, [], **kwargs)
        bazzes = kwargs['bundles'][0]['obj'].bazzes.all()
        self.assertEqual(bazzes.count(), 2)

    def test_delete_detail(self):
        bar = self.resource.Meta.model(name='new bar')
        bar.save()
        kwargs = {
            'pub': ['delete', 'detail'],
            'objs': [bar]
        }
        delete_detail = self.factory.delete('/bar/1/')
        request, args, kwargs = self.resource.delete_detail(delete_detail, [], **kwargs)
        self.assertRaises(ObjectDoesNotExist, Bar.objects.get, pk=bar.id)

    def test_dehydrate_explicit_fields(self):
        class BazResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = Baz
                api = Api(name='v1')

        class FooResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = Foo
                api = Api(name='v1')

            class Fields:
                bazzes = ManyToManyField(attribute='bazzes', resource_cls=BazResource, embed=True)

        foo_resource = FooResource()
        foo_dict = {
            'name': 'zed',
            'text': '',
            'integer': 9,
            'float_field': 123.123,
            'boolean': True,
            'decimal': '12.34',
            'file_field': 'test.mov',
            }
        foo = Foo(**foo_dict)
        foo.save()
        baz = Baz.objects.create(name='baz 1')
        foo.bazzes.add(baz)

        bundles = [{
            'obj': foo,
            'response_data': {}
        }]

        kwargs = {
            'bundles': bundles,
            'pub': ['get', 'detail']
        }
        get_detail = self.factory.get('/foo/1')
        request, args, kwargs = foo_resource.dehydrate_explicit_fields(get_detail, [], **kwargs)

        bazzes = kwargs['bundles'][0]['response_data']['bazzes']

        self.assertTrue('name' in bazzes[0])

    def test_add_resource_uri(self):
        bar = Bar(name='new bar')
        bar.save()
        kwargs = {
            'pub': ['get', 'list'],
            'bundles': [{
                'obj': bar,
                'response_data': {}
            }]
        }
        get_list = self.factory.get('/bar/')
        request, args, kwargs = self.resource.add_resource_uri(get_list, [], **kwargs)

        data = kwargs['bundles'][0]['response_data']
        self.assertEqual(data['resource_uri'], '/api/{0}/bar/{1}/'.format(self.resource.Meta.api.name, bar.pk))

