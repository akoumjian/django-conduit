import json

from django.contrib.contenttypes.models import ContentType

from conduit.api import Api
from conduit.test.testcases import ConduitTestCase

from api.views import BarResource, ContentTypeResource, FooResource, ItemResource

from example.models import Bar, Baz, Foo, Item


class ResourceTestCase(ConduitTestCase):
    def test_create_resource(self):
        obj = {
            'name': 'A new Bar'
        }
        data = json.dumps(obj)
        post_list = self.factory.post('/bar/', data, content_type='application/json')
        
        bar_resource = BarResource()
        bar_resource.Meta.api = Api(name='v1')

        response = bar_resource.view(post_list, [], {})
        content = json.loads(response.content)

        bar = Bar.objects.get(id=content['id'])

        self.assertEqual(bar.name, obj['name'])
        self.assertEqual(Bar.objects.count(), 1)

    def test_create_fk_resource(self):
        obj = {
            'bar': {
                'name': 'New Bar',
            },
            'bazzes': [
                {
                    'name': 'New Baz'
                },
                {
                    'name': 'Another Baz'
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
        data = json.dumps(obj)
        post_list = self.factory.post('/foo/', data, content_type='application/json')

        foo_resource = FooResource()
        foo_resource.Meta.api = Api(name='v1')

        response = foo_resource.view(post_list, [], {})
        content = json.loads(response.content)

        self.assertEqual(Bar.objects.count(), 1)
        self.assertEqual(Baz.objects.count(), 2)
        self.assertEqual(Foo.objects.count(), 1)

    def test_create_gfk_resource(self):
        content_type = ContentType.objects.get(name='bar')

        obj_data = {
            'object_id': 1,
            'content_type': '/api/v1/contenttype/8/'
        }
        data = json.dumps(obj_data)

        post_detail = self.factory.post('/item/', data, content_type='application/json')

        item_resource = ItemResource()
        item_resource.Meta.api = Api(name='v1')

        response = item_resource.view(post_detail, [], {})

        self.assertEqual(Item.objects.count(), 1)

    def test_gfk_resource_detail(self):
        bar = Bar.objects.create(name='A bar')
        content_type = ContentType.objects.get(name='bar')
        item = Item.objects.create(
            object_id=bar.id,
            content_type=content_type
        )

        item_resource = ItemResource()

        get_detail = self.factory.get('/item/1/', content_type='application/json')
        response = item_resource.view(get_detail, [], {})
        content = json.loads(response.content)

        meta = content['meta']
        objects = content['objects']

        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(meta['total'], 1)
        self.assertEqual(objects[0]['id'], bar.id)
        self.assertEqual(objects[0]['object_id'], bar.id)
        self.assertEqual(objects[0]['content_type'], '/api/v1/contenttype/8/')
        self.assertEqual(objects[0]['content_object'], '/api/v1/bar/{0}/'.format(bar.id))
        self.assertEqual(objects[0]['resource_uri'], '/api/v1/item/1/')
