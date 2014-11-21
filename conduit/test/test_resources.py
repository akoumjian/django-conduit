import json

from django.contrib.contenttypes.models import ContentType

from conduit.api import Api
from conduit.test.testcases import ConduitTestCase

from api.views import BarResource, ContentTypeResource, FooResource, ItemResource

from example.models import Bar, Baz, Foo, Item


class ResourceTestCase(ConduitTestCase):
    def test_gfk_post_list(self):
        item_resource = ItemResource()
        item_resource.Meta.api = Api(name='v1')
        item_uri = item_resource._get_resource_uri()

        content_type = ContentType.objects.get(name='bar')

        obj_data = {
            'content_type': content_type.id,
            'content_object': {
                'name': 'Bar name'
            }
        }

        resposne = self.client.post(
            item_uri,
            data=json.dumps(obj_data),
            content_type='application/json'
        )

        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Item.objects.get(id=1).content_object.id, 1)
        self.assertEqual(Bar.objects.count(), 1)
        self.assertEqual(Bar.objects.all()[0].name, 'Bar name')

    def test_gfk_get_detail(self):
        bar_resource = BarResource()
        item_resource = ItemResource()

        content_type = ContentType.objects.get(name='bar')
        bar = Bar.objects.create(name='A bar')
        item = Item.objects.create(
            object_id=bar.id,
            content_type=content_type
        )

        bar_uri = bar_resource._get_resource_uri(obj=bar)
        item_uri = item_resource._get_resource_uri(obj=item)

        response = self.client.get(item_uri)
        content = json.loads(response.content.decode())

        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Bar.objects.count(), 1)
        self.assertEqual(content['resource_uri'], item_uri)
        self.assertEqual(content['object_id'], item.object_id)
        self.assertEqual(content['id'], item.id)
        self.assertEqual(content['content_object']['resource_uri'], bar_uri)

    def test_gfk_update_detail(self):
        bar = Bar.objects.create(name='Bar name')
        content_type = ContentType.objects.get(name='bar')
        item = Item.objects.create(
            content_type=content_type,
            object_id=bar.id
        )

        item_resource = ItemResource()
        item_resource.Meta.api = Api(name='v1')
        item_uri = item_resource._get_resource_uri(obj=item)

        bar_resource = BarResource()
        bar_uri = bar_resource._get_resource_uri(obj=bar)

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
        content_type = ContentType.objects.get(name='bar')
        item = Item.objects.create(
            object_id=bar.id,
            content_type=content_type
        )
        response = self.client.delete('/api/v1/item/1/')

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Item.objects.count(), 0)
