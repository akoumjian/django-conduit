import json

from datetime import datetime

from django.contrib.contenttypes.models import ContentType

from conduit.api import Api
from conduit.test.testcases import ConduitTestCase

from api.views import BarResource, ContentTypeResource, FooResource, ItemResource

from example.models import Bar, Baz, Foo, Item


class ResourceTestCase(ConduitTestCase):
    def setUp(self):
        self.item_resource = ItemResource()

        self.bar_resource = BarResource()

        self.foo_resource = FooResource()

        api = Api(name='v1')
        api.register(self.item_resource)
        api.register(self.bar_resource)
        api.register(self.foo_resource)

        self.bar_ctype = ContentType.objects.get(name='bar')

    def test_gfk_post_list(self):
        data = [
            {
                'content_type': self.bar_ctype.id,
                'content_object': {
                    'name': 'Bar name one'
                }
            },
            {
                'content_type': self.bar_ctype.id,
                'content_object': {
                    'name': 'Bar name two'
                }
            }
        ]

        item_uri = self.item_resource._get_resource_uri()
        response = self.client.post(
            item_uri,
            json.dumps(data),
            content_type='application/json'
        )
        content = json.loads(response.content.decode())

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Item.objects.count(), 2)
        self.assertEqual(Bar.objects.count(), 2)

        item_1 = Item.objects.get(id=content[0]['object_id'])
        item_2 = Item.objects.get(id=content[1]['object_id'])

        self.assertEqual(item_1.content_object.name, 'Bar name one')
        self.assertEqual(item_2.content_object.name, 'Bar name two')

    def test_gfk_embed(self):
        data = [
            {
                'content_type': self.bar_ctype.id,
                'content_object': {
                    'name': 'Bar name one'
                }
            }
        ]
        item_uri = self.item_resource._get_resource_uri()
        self.client.post(
            item_uri,
            json.dumps(data),
            content_type='application/json'
        )

        bar = Bar.objects.get(name='Bar name one')
        ctype = ContentType.objects.get(name='bar')
        response = self.client.get(item_uri)
        content = json.loads(response.content.decode())

        self.assertEqual(content['meta']['total'], 1)

        bar_resource = content['objects'][0]
        self.assertEqual(bar_resource['object_id'], bar.id)
        self.assertEqual(bar_resource['content_type'], ctype.id)

        self.assertIsInstance(bar_resource['content_object'], dict)
        self.assertEqual(bar_resource['content_object']['id'], bar.id)
        self.assertEqual(bar_resource['content_object']['name'], bar.name)
        self.assertEqual(bar_resource['content_object']['resource_uri'], '/api/v1/bar/1/')

    def test_gfk_get_detail(self):
        bar = Bar.objects.create(name='A bar')
        item = Item.objects.create(
            object_id=bar.id,
            content_type=self.bar_ctype
        )

        bar_uri = self.bar_resource._get_resource_uri(obj=bar)
        no_map_item_resource = ItemResource()
        no_map_item_resource.resource_map = {}
        item_uri = no_map_item_resource._get_resource_uri(obj=item)

        response = self.client.get(item_uri)
        content = json.loads(response.content.decode())

        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Bar.objects.count(), 1)
        self.assertEqual(content['resource_uri'], item_uri)
        self.assertEqual(content['object_id'], item.object_id)
        self.assertEqual(content['id'], item.id)
        self.assertEqual(content['content_object']['resource_uri'], bar_uri)

    def test_gfk_get_detail_no_resource_map(self):
        bar = Bar.objects.create(name='A bar')
        item = Item.objects.create(
            object_id=bar.id,
            content_type=self.bar_ctype
        )

        bar_uri = self.bar_resource._get_resource_uri(obj=bar)
        item_uri = self.item_resource._get_resource_uri(obj=item)

        response = self.client.get(item_uri)
        content = json.loads(response.content.decode())

        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Bar.objects.count(), 1)
        self.assertEqual(content['resource_uri'], item_uri)
        self.assertEqual(content['object_id'], item.object_id)
        self.assertEqual(content['id'], item.id)
        self.assertEqual(content['content_object']['resource_uri'], bar_uri)

    def test_gfk_update_list(self):
        bar_1 = Bar.objects.create(name="Bar one")
        bar_2 = Bar.objects.create(name="Bar two")

        item_1 = Item.objects.create(
            content_type=self.bar_ctype,
            object_id=bar_1.id
        )

        item_2 = Item.objects.create(
            content_type=self.bar_ctype,
            object_id=bar_2.id
        )

        data = [
            {
                'resource_uri': self.item_resource._get_resource_uri(obj=item_1),
                'id': item_1.id,
                'content_type': item_1.content_type.id,
                'content_object': {
                    'resource_uri': self.bar_resource._get_resource_uri(obj=bar_1),
                    'id': bar_1.id,
                    'name': 'Altered bar 1'
                }
            },
            {
                'resource_uri': self.item_resource._get_resource_uri(obj=item_2),
                'id': item_2.id,
                'content_type': item_2.content_type.id,
                'content_object': {
                    'resource_uri': self.bar_resource._get_resource_uri(obj=bar_2),
                    'id': bar_2.id,
                    'name': 'Altered bar 2'
                }
            }
        ]

        item_uri = self.item_resource._get_resource_uri()
        response = self.client.put(item_uri, json.dumps(data))
        content = response.content.decode()

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Bar.objects.count(), 2)
        self.assertEqual(Item.objects.count(), 2)

        self.assertEqual(Bar.objects.get(id=bar_1.id).name, 'Altered bar 1')
        self.assertEqual(Bar.objects.get(id=bar_2.id).name, 'Altered bar 2')

    def test_gfk_update_detail(self):
        bar = Bar.objects.create(name='Bar name')
        item = Item.objects.create(
            content_type=self.bar_ctype,
            object_id=bar.id
        )

        item_uri = self.item_resource._get_resource_uri(obj=item)
        bar_uri = self.bar_resource._get_resource_uri(obj=bar)

        data = {
            'resource_uri': item_uri,
            'id': item.id,
            'content_type': item.content_type.id,
            'content_object': {
                'resource_uri': bar_uri,
                'id': bar.id,
                'name': 'New bar name'
            }
        }

        response = self.client.put(item_uri, json.dumps(data))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Bar.objects.get(id=bar.id).name, 'New bar name')
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Bar.objects.count(), 1)

    def test_gfk_delete_detail(self):
        bar = Bar.objects.create(name='Delete bar')
        item = Item.objects.create(
            object_id=bar.id,
            content_type=self.bar_ctype
        )

        delete_endpoint = self.item_resource._get_resource_uri(obj=item)
        response = self.client.delete(delete_endpoint)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Item.objects.count(), 0)

    def test_gfk_foo_resource(self):
        data = {
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

        foo_list_uri = self.foo_resource._get_resource_uri()
        response = self.client.post(
            foo_list_uri,
            json.dumps(data),
            content_type='application/json'
        )
        content = json.loads(response.content.decode())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Foo.objects.count(), 1)

        foo_get_uri = self.foo_resource._get_resource_uri(obj=Foo.objects.get(id=content['id']))
        response = self.client.get(foo_get_uri)
        content = json.loads(response.content.decode())

        self.assertEqual(
            Bar.objects.get(id=content['bar']['id']).name,
            'New Bar'
        )

        self.assertEqual(
            Baz.objects.get(id=content['bazzes'][0]['id']).name,
            'New Baz'
        )

        self.assertEqual(
            Baz.objects.get(id=content['bazzes'][1]['id']).name,
            'Another Baz'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['birthday'], datetime.now().strftime('%Y-%m-%d')) # '2013-06-19'
        self.assertEqual(content['boolean'], False)

        frmt = '%Y-%m-%dT%H:%M:%S.%f'
        # `content['created'][:-6]` rips out the timezone information for parsing
        self.assertEqual(
            datetime.strftime(datetime.strptime(content['created'][:-6], frmt), frmt),
            datetime.strftime(Foo.objects.all()[0].created, frmt)
        )
        self.assertEqual(content['decimal'], '110.12')
        self.assertEqual(content['file_field'], 'test/test.txt')
        self.assertEqual(content['float_field'], 100000.123456789)
        self.assertEqual(content['id'], 1)
        self.assertEqual(content['integer'], 12)
        self.assertEqual(content['name'], 'Foo Name')
        self.assertEqual(content['text'], 'text goes here')
