Filtering and Ordering
======================

During a get list view, it is useful to be able to filter or rearrange the results. Django-Conduit provides a few helpful properties and hooks to to filter your resources.

Server Side Filters to Limit Access
-----------------------------------

The ``default_filters`` dict on a ModelResource's Meta class will apply the listed queryset filters before fetching results. The keys in ``default_filters`` ought to be a valid Queryset filter method for the specified model. Here is an example that only returns Foo objects that have a name starting with the the word 'lamp'::

	class FooResource(ModelResource):
		class Meta(ModelResource.Meta):
			default_filters = {
				'name__startswith': 'lamp'
			}

The default filters will eventually be applied to the queryset during the ``pre_get_list`` method, resulting in something like this::

	filtered_instances = Foo.objects.filter(name__startswith='lamp')


Client Side Filtering with Get Params
-------------------------------------

API consumers often need to be able to filter against certain resource fields using GET parameters. Filtering is enabled by specifying the ``allowed_filters`` array. The array takes a series of Queryset filter keywords::

	class FooResource(ModelResource):
		class Meta(ModelResource.Meta):
			allowed_filters = [
				'name__icontains',
				'created__lte',
				'created__gte',
				'bar__name'
			]

In the above example, API consumers will be allowed to get Foo objects by searching for strings in the Foo name, or by finding Foos created before or after a given datetime.

.. note:: Each Queryset filter has to be specified using the entire filter name. While verbose, this allows custom or related field parameters such as ``bar__name`` to be easily specified.


Ordering Results
----------------

If you want to specify the default order for objected, returned, you can simply specify the ``order_by`` string using the ``default_ordering`` Meta field::

	class FooResource(ModelResource):
		class Meta(ModelResource.Meta):
			default_ordering='-created'

The value of ``default_ordering`` should be the same one you would use when performing order_by on a queryset. The above example will result in the following operation::

	Foo.objects.order_by('-created')

To allow API consumers to order the results, the ``allowed_ordering`` field is an array of valid ordering keys::

	class FooResource(ModelResource):
		class Meta(ModelResource.Meta):
			allowed_ordering = [
				'created',
				'-created'
			]

Note how the forward and reverse string both have to be specified. This is to provide precise control over client ordering values.


How Filters & Ordering are Applied
----------------------------------

Filtering and ordering happens inside two steps in the default conduit pipeline. The first happens inside ``process_filters``. To determine order, first the method looks for an order_by GET parameter. If none are specified, it defaults to the ``default_ordering`` attribute. If the order_by parameter is not a valid value, the client receives a 400.

The filters start with the ``default_filters`` dictionary. This dictionary is then updated from filters specified in the GET parameters, provided they are specified in ``allowed_filters``. 

After the order_by and filters are determined, their values are sent forward in the kwargs dictionary where they are picked up again in ``pre_get_list``. This is the method that first applies the ``kwargs['order_by']`` value, and then applies the values inside ``kwargs['filters']``. It stores the ordered and filtered queryset inside of ``kwargs['objs']``. The objects are then subject to authorization limits and paginated inside ``get_list`` before the final set of objects is determined.