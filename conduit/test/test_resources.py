import json

from django.contrib.contenttypes.models import ContentType

from conduit.api import Api
from conduit.test.testcases import ConduitTestCase

from api.views import BarResource, ContentTypeResource, FooResource, ItemResource

from example.models import Bar, Baz, Foo, Item


class ResourceTestCase(ConduitTestCase):
    def setUp(self):
        self.item_resource = ItemResource()
        self.item_resource.Meta.api = Api(name='v1')

        self.bar_resource = BarResource()
        self.bar_resource.Meta.api = Api(name='v1')

        self.bar_ctype = ContentType.objects.get(name='bar')

    def test_gfk_post_list(self):
        item_uri = self.item_resource._get_resource_uri()

        data = {
            'content_type': self.bar_ctype.id,
            'content_object': {
                'name': 'Bar name'
            }
        }

        resposne = self.client.post(
            item_uri,
            json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Item.objects.get(id=1).content_object.id, 1)
        self.assertEqual(Bar.objects.count(), 1)
        self.assertEqual(Bar.objects.all()[0].name, 'Bar name')

    def test_gfk_get_detail(self):
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
