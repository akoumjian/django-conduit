import datetime
import dateutil
from decimal import Decimal
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import Point, LineString, Polygon, MultiPolygon
from django.contrib.gis.geos import fromstr
from conduit.api import ModelResource, Api
from conduit.api.fields import ForeignKeyField, ManyToManyField
from conduit.exceptions import HttpInterrupt
from geoexample.models import GeoBar, GeoFoo, GeoBaz
from conduit.test.testcases import ConduitTestCase


class GeoMethodTestCase(ConduitTestCase):

    def setUp(self):
        class TestResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = GeoBar
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


        #
        #  setup a specific geodjango resource to test
        #
        class GeoTestResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = GeoBar
                default_filters = {
                }
                #  only test some of the default geometry filters
                allowed_filters = [
                    'geom__bbcontains',
                    'geom__contains',
                    'geom__intersects',
                ]
                allowed_ordering = [
                ]
        self.georesource = GeoTestResource()
        self.georesource.Meta.api = Api(name='v1')

        #
        #  setup some default geom types to use throughout tests
        #
        self.point = Point(-122.306814, 47.266380)
        self.line = LineString( (-123.296814,47.066380), (-121.324768,48.370848) )
        self.poly = Polygon( ((-123.296814,47.066380), (-123.296814,48.370848), (-121.324768,48.370848), (-121.324768,47.066380), (-123.296814,47.066380)) )
        self.poly2 = Polygon( ((0, 0), (0, 1), (1, 1), (0, 0)) )
        self.multipoly = MultiPolygon( self.poly, self.poly2 )

    def test_build_pub(self):
        detail_get = self.factory.get('/geofoo/1/')
        list_get = self.factory.get('/geofoo/')
        put_detail = self.factory.put('/geofoo/1/', {})

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

        get = self.factory.get('/geofoo/')
        put = self.factory.put('/geofoo/', {})
        post = self.factory.post('/geofoo/', {})
        delete = self.factory.delete('/geofoo')

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
        instance = self.resource.Meta.model(geom=self.point)
        instance.save()

        pk_field = self.resource.Meta.pk_field
        kwargs = {
            'pub': ['detail'],
            pk_field: instance.pk
        }

        request, args, kwargs = self.resource.get_object_from_kwargs(None, [], **kwargs)
        self.assertIn(instance, kwargs['objs'])

    def test_process_filters(self):
        list_get = self.factory.get('/geofoo/?name__lte=delta&order_by=-name')
        kwargs = {
            'pub': ['get']
        }
        request, args, kwargs = self.resource.process_filters(list_get, [], **kwargs)
        filters = kwargs['filters']
        self.assertEqual(filters.get('name__gte', None), 'beta', msg='Default filter was not included')
        self.assertEqual(filters.get('name__lte', None), 'delta', msg='Param filters should override default filters')
        self.assertEqual(kwargs.get('order_by', None), '-name', msg='Ordering was not added to kwargs')

    def test_invalid_filter(self):
        list_get = self.factory.get('/geofoo/?name__lt=delta')
        kwargs = {
            'pub': ['get']
        }
        self.assertRaises(
            HttpInterrupt,
            self.resource.process_filters,
            list_get, **kwargs
        )

    def test_invalid_order_by(self):
        list_get = self.factory.get('/geofoo/?order_by=name')
        kwargs = {
            'pub': ['get']
        }
        self.assertRaises(
            HttpInterrupt,
            self.resource.process_filters,
            list_get, **kwargs
        )

    def test_process_filters_geom_bbcontains(self):
        import json
        GeoBar.objects.all().delete() # delete all for easy testing
        geobar = GeoBar(name='new geobar', geom=self.poly)
        geobar.save()

        #
        # TODO: GET requests using WKT geoms will definitely push the URL max-length limit
        # and since they can be expensive, they are potentially harmful on large geometries
        # 
        list_get = self.factory.get('/geobar/?geom__bbcontains='+self.point.wkt)
        kwargs = {
            'pub': ['get', 'list']
        }
        request, args, kwargs = self.georesource.process_filters(list_get, [], **kwargs)
        kwargs.update( **{ 'filters' : kwargs[ 'filters' ] } )
        request, args, kwargs = self.georesource.apply_filters(list_get, [], **kwargs)
        self.assertEqual( kwargs[ 'total_count' ], 1)

    def test_process_filters_geom_contains(self):
        import json
        GeoBar.objects.all().delete() # delete all for easy testing
        geobar = GeoBar(name='new geobar', geom=self.poly)
        geobar.save()

        #
        # TODO: GET requests using WKT geoms will definitely push the URL max-length limit
        # and since they can be expensive, they are potentially harmful on large geometries
        # 
        list_get = self.factory.get('/geobar/?geom__contains='+self.point.wkt)
        kwargs = {
            'pub': ['get', 'list']
        }
        request, args, kwargs = self.georesource.process_filters(list_get, [], **kwargs)
        kwargs.update( **{ 'filters' : kwargs[ 'filters' ] } )
        request, args, kwargs = self.georesource.apply_filters(list_get, [], **kwargs)
        self.assertEqual( kwargs[ 'total_count' ], 1)

    def test_process_filters_geom_intersects(self):
        import json
        GeoBar.objects.all().delete() # delete all for easy testing
        geobar = GeoBar(name='new geobar', geom=self.poly)
        geobar.save()

        #
        # TODO: GET requests using WKT geoms will definitely push the URL max-length limit
        # and since they can be expensive, they are potentially harmful on large geometries
        # 
        list_get = self.factory.get('/geobar/?geom__intersects='+self.point.wkt)
        kwargs = {
            'pub': ['get', 'list']
        }
        request, args, kwargs = self.georesource.process_filters(list_get, [], **kwargs)
        kwargs.update( **{ 'filters' : kwargs[ 'filters' ] } )
        request, args, kwargs = self.georesource.apply_filters(list_get, [], **kwargs)
        self.assertEqual( kwargs[ 'total_count' ], 1)

    def test_json_to_python(self):
        import json
        py_data = {
            'fieldname': 'fieldvalue',
        }
        data = json.dumps(py_data)
        detail_put = self.factory.put('/geobar/1/', data, content_type='application/json')
        kwargs = {
            'pub': ['put']
        }
        request, args, kwargs = self.resource.json_to_python(detail_put, data, **kwargs)
        self.assertEqual(kwargs.get('request_data', None), py_data)

    def test_hydrate_request_data(self):
        self.resource.Meta.model = GeoFoo
        post_hydrate_data = {
            'geobar': {
                'name': 'New GeoBar',
            },
            'geobazzes': [
                {
                    'name': 'New GeoBaz'
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
            'name': 'GeoFoo Name',
            'text': 'text goes here'
        }

        request_data = {
            'geobar': {
                'name': 'New GeoBar',
            },
            'geobazzes': [
                {
                    'name': 'New GeoBaz',
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
            'name': 'GeoFoo Name',
            'text': 'text goes here'
        }
        kwargs = {
            'request_data': [request_data],
            'pub': ['post', 'list']
        }
        post_list = self.factory.post('/geofoo/')
        request, args, kwargs = self.resource.hydrate_request_data(post_list, **kwargs)
        self.assertEqual([post_hydrate_data], kwargs['request_data'])

    def test_form_validate(self):
        class GeoBarForm(forms.ModelForm):
            class Meta:
                model = GeoBar

            def clean_name(self):
                data = self.cleaned_data['name']
                raise forms.ValidationError('Fake validation error', code='fake')
                return data
        self.resource.Meta.form_class = GeoBarForm
        geobar = GeoBar.objects.create(geom=self.point)
        kwargs = {
            'pub': ['post', 'list'],
            'bundles': [
                {
                    'obj': geobar,
                    'request_data': {
                        'name': 'whatevs',
                        'geom': self.poly.wkt,
                        'resource_uri': '/api/v1/geobar/{0}'.format(geobar.pk),
                        'random_field': 'geofoogeobar'
                    }
                }
            ]
        }

        post_list = self.factory.post('/geobar/')

        self.assertRaises(HttpInterrupt, self.resource.form_validate, post_list, [], **kwargs)

    def test_get_detail(self):
        get_detail = self.factory.get('/geofoo/1/')
        kwargs = {
            'pub': ['get', 'detail']
        }
        request, args, kwargs = self.resource.get_detail(get_detail, [], **kwargs)
        self.assertEqual(kwargs['status'], 200)

    def test_save_fk_objs(self):
        class GeoFooResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = GeoFoo
            class Fields:
                geobar = ForeignKeyField(attribute='geobar', resource_cls=self.resource.__class__, embed=True)

        geofoo_resource = GeoFooResource()
        geofoo = GeoFoo(
            **{ 'name': 'zed',
                'text': '',
                'integer': 9,
                'float_field': 123.123,
                'boolean': True,
                'geom' : self.line.wkt,
                'decimal': '12.34',
                'file_field': 'test.mov',
            }
        )
        geofoo.save()
        post_list = self.factory.post('/geofoo/')
        kwargs = {
            'pub': ['post', 'list'],
            'bundles': [{
                'request_data': {
                    'name': 'geofoo name',
                    'geobar': {
                        'name': 'geobar name',
                        'geom': self.point.wkt
                    },
                },
                'obj': geofoo
            }],
        }
        request, args, kwargs = geofoo_resource.save_fk_objs(post_list, [], **kwargs)
        self.assertEqual(kwargs['bundles'][0]['obj'].geobar.name, 'geobar name')

    def test_save_m2m_objs(self):
        class GeoBazResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = GeoBaz

        class GeoFooResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = GeoFoo
            class Fields:
                geobazzes = ManyToManyField(attribute='geobazzes', resource_cls=GeoBazResource, embed=True)

        geofoo_resource = GeoFooResource()
        geofoo = GeoFoo(
            **{ 'name': 'zed',
                'text': '',
                'integer': 9,
                'float_field': 123.123,
                'boolean': True,
                'decimal': '12.34',
                'geom' : self.poly.wkt,
                'file_field': 'test.mov',
            }
        )
        geofoo.save()
        post_list = self.factory.post('/geofoo/')
        kwargs = {
            'pub': ['post', 'list'],
            'bundles': [{
                'request_data': {
                    'name': 'geofoo name',
                    'geobazzes': [
                        {'name': 'geobaz 1', 'geom' : self.point.wkt }, {'name': 'geobaz 2', 'geom' : self.poly.wkt }
                    ]
                },
                'obj': geofoo
            }]
        }
        request, args, kwargs = geofoo_resource.save_m2m_objs(post_list, [], **kwargs)
        geobazzes = kwargs['bundles'][0]['obj'].geobazzes.all()
        self.assertEqual(geobazzes.count(), 2)

    def test_delete_detail(self):
        geobar = self.resource.Meta.model(name='new geobar',geom=self.point)
        geobar.save()
        kwargs = {
            'pub': ['delete', 'detail'],
            'objs': [geobar]
        }
        delete_detail = self.factory.delete('/geobar/1/')
        request, args, kwargs = self.resource.delete_detail(delete_detail, [], **kwargs)
        self.assertRaises(ObjectDoesNotExist, GeoBar.objects.get, pk=geobar.id)

    def test_dehydrate_explicit_fields(self):
        class GeoBazResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = GeoBaz
                api = Api(name='v1')

        class GeoFooResource(ModelResource):
            class Meta(ModelResource.Meta):
                model = GeoFoo
                api = Api(name='v1')

            class Fields:
                geobazzes = ManyToManyField(attribute='geobazzes', resource_cls=GeoBazResource, embed=True)

        geofoo_resource = GeoFooResource()
        geofoo_dict = {
            'name': 'zed',
            'text': '',
            'integer': 9,
            'float_field': 123.123,
            'boolean': True,
            'geom' : self.poly.wkt,
            'decimal': '12.34',
            'file_field': 'test.mov',
            }
        geofoo = GeoFoo(**geofoo_dict)
        geofoo.save()
        geobaz = GeoBaz.objects.create(name='geobaz 1', geom=self.point)
        geofoo.geobazzes.add(geobaz)

        bundles = [{
            'obj': geofoo,
            'response_data': {}
        }]

        kwargs = {
            'bundles': bundles,
            'pub': ['get', 'detail']
        }
        get_detail = self.factory.get('/geofoo/1')
        request, args, kwargs = geofoo_resource.dehydrate_explicit_fields(get_detail, [], **kwargs)

        geobazzes = kwargs['bundles'][0]['response_data']['geobazzes']

        self.assertTrue('name' in geobazzes[0])

    def test_add_resource_uri_point(self):
        geobar = GeoBar(name='new geobar',geom=self.point)
        geobar.save()
        kwargs = {
            'pub': ['get', 'list'],
            'bundles': [{
                'obj': geobar,
                'response_data': {}
            }]
        }
        get_list = self.factory.get('/geobar/')
        request, args, kwargs = self.resource.add_resource_uri(get_list, [], **kwargs)

        data = kwargs['bundles'][0]['response_data']
        self.assertEqual(data['resource_uri'], '/api/{0}/geobar/{1}/'.format(self.resource.Meta.api.name, geobar.pk))

    def test_add_resource_uri_poly(self):
        geobar = GeoBar(name='new geobar',geom=self.poly)
        geobar.save()
        kwargs = {
            'pub': ['get', 'list'],
            'bundles': [{
                'obj': geobar,
                'response_data': {}
            }]
        }
        get_list = self.factory.get('/geobar/')
        request, args, kwargs = self.resource.add_resource_uri(get_list, [], **kwargs)

        data = kwargs['bundles'][0]['response_data']
        self.assertEqual(data['resource_uri'], '/api/{0}/geobar/{1}/'.format(self.resource.Meta.api.name, geobar.pk))


    def test_add_resource_uri_multipoly(self):
        geobar = GeoBar(name='new geobar',geom=self.multipoly)
        geobar.save()
        kwargs = {
            'pub': ['get', 'list'],
            'bundles': [{
                'obj': geobar,
                'response_data': {}
            }]
        }
        get_list = self.factory.get('/geobar/')
        request, args, kwargs = self.resource.add_resource_uri(get_list, [], **kwargs)

        data = kwargs['bundles'][0]['response_data']
        self.assertEqual(data['resource_uri'], '/api/{0}/geobar/{1}/'.format(self.resource.Meta.api.name, geobar.pk))




