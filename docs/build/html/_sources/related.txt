Related Resources & Objects
===========================

``django-conduit`` treats related ForeignKey and ManyToMany objects in an intuitive and efficient manner. You can use related resources to treat them similarly to related models, or you can default to their simple behavior as pointers to primary keys.

Default Behavior
================

By default, conduit will serialize your model's related object fields by their raw value. A ForeignKey field will produce the primary key of your related object. A ManyToMany field will product a list of primary keys.

An example resource Foo has one FK and one M2M field::

	class Foo(models.Model):
		name = models.CharField(max_length=255)
		bar = models.ForeignKey(Bar)
		bazzes = models.ManyToManyField(Baz)

Will produce a detail response looking like this::

	{
		"name": "My Foo",
		"bar": 45,
		"bazzes": [5, 87, 200],
		"resource_uri": "/api/v1/foo/1/"
	}

When updating a ForeignKey field, conduit will set the model's [field]_id to the integer you send it. Be careful not to set it to a nonexistent related model, since there are not constraint checks done when saved to the database.

Similarly, when updated a ManyToMany field and give it a nonexistent primary key, the add will silently fail and the invalid primary key will not enter the ManyToMany list.

.. important:: Updating raw primary keys will not produce errors for invalid keys. 


Related Resource Fields
=======================

A much more useful approach is to point to a related ModelResource for your related fields. You can use a related resource by referencing it in the Fields metaclass. The below FooResource example using two related resource fields::

	class FooResource(ModelResource):
	    class Meta(ModelResource.Meta):
	        model = Foo
	    class Fields:
	        bar = ForeignKeyField(attribute='bar', resource_cls='api.views.BarResource')
	        bazzes = ManyToManyField(attribute='bazzes', resource_cls='api.views.BazResource', embed=True)

	class BarResource(ModelResource):
	    class Meta(ModelResource.Meta):
	        model = Bar


	class BazResource(ModelResource):
	    class Meta(ModelResource.Meta):
	        model = Baz

Using a related resource lets you embed the entire resource data inside of the parent resource. One of the resources above is set to embed=True, while the other is not and will default to the ``resource_uri``. An example of the above FooResource would look like this::

	{
	    "bar": "/api/v1/bar/23/",
	    "name": "stuffs",
	    "id": 1,
	    "bazzes": [
	        {
	            "resource_uri": "/api/v1/baz/1/",
	            "id": 1,
	            "name": "Baz 1"
	        },
	        {
	            "resource_uri": "/api/v1/baz/7/",
	            "id": 7,
	            "name": "Baz 7"
	        }
	    ],
	    "resource_uri": "/api/v1/foo/1/"
	}

Updating Related Resources
--------------------------

The **real** power of using related resources is that they follow the rules of the resource they point to. Using our previous example, let's say you update one of the Baz objects in place and then send a PUT to our parent resource at ``/api/v1/foo/1/``::

	{
		...
	    "bazzes": [
	        {
	            "resource_uri": "/api/v1/baz/1/",
	            "id": 1,
	            "name": "MODIFIED BAZ NAME"
	        },
	        {
	            "resource_uri": "/api/v1/baz/7/",
	            "id": 7,
	            "name": "Baz 7"
	        }
	    ],
	    ...
	}

The Baz object with id == 1 will now have the name "MODIFIED BAZ NAME" unless the BazResource determines the request is not authorized (using the methods described in `Access & Authorization<access_authorization>`) or if the data doesn't validate, etc.

If you include data for a related resource without a primary key, it will created the related object for you and add it to the parent resource object. For example, if you send a PUT to our /api/v1/foo/1/ resource with the following data::


	{
		...
	    "bazzes": [
	        {
	            "resource_uri": "/api/v1/baz/1/",
	            "id": 1,
	            "name": "MODIFIED BAZ NAME"
	        },
	        {
	            "resource_uri": "/api/v1/baz/7/",
	            "id": 7,
	            "name": "Baz 7"
	        },
	        {
	            "name": "New Baz"
	        }
	    ],
	    ...
	}

The related BazResource will attempt to create a new Baz as if you had sent a POST to ``/api/v1/baz/``. Then it will add the new Baz object to Foo's ManyToMany field. In the return response, the object will be filled in with its new id and resource_uri.

Similarly if you PUT to ``/api/v1/foo/1/`` and omit one of the existing Baz objects, it will remove it from the ManyToMany field. It will NOT delete the Baz object, however::

	{
		...
	    "bazzes": [
	        {
	            "resource_uri": "/api/v1/baz/1/",
	            "id": 1,
	            "name": "MODIFIED BAZ NAME"
	        }
	    ],
	    ...
	}

The above request will remove all but the Baz 1 object from Foo's bazzes field.


Customizing Related Resource Fields
-----------------------------------

The default ForeignKeyField and ManyToManyField that ship with Conduit can easily be subclassed and customized. The fields work very similarly to ModelResources, except instead of a single Meta.conduit pipeline, they have two pipelines. One if for updating from request data, and the other is for fetching the existing resource.

A subclassed FK field which adds a custom additional step to the pipeline would look like this::

	class CustomForeignKeyField(ForeignKeyField):
	    dehydrate_conduit = (
	        'objs_to_bundles',
	        ## Adds a custom step when grabbing and object
	        ## and turning it to json data
	        'myapp.resources.CustomResource.custom_method'
	        'add_resource_uri',
	    )

	    save_conduit = (
	        'check_allowed_methods',
	        'get_object_from_kwargs',
	        'hydrate_request_data',
	        ## Adds a custom step when preparing data
	        ## for updating / creating new object
	        'myapp.resources.CustomResource.custom_method'
	        'initialize_new_object',
	        'save_fk_objs',
	        'auth_put_detail',
	        'auth_post_detail',
	        'form_validate',
	        'put_detail',
	        'post_list',
	        'save_m2m_objs',
	    )

