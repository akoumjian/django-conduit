Conduit Overview
=================

What is a Conduit?
-------------------

Conduits are views that send requests through a simple list of functions to produce a response. This process is often called a pipeline (hence the name conduit). Here is an example::

    conduit = (
        'deserialize_json',
        'run_form_validation',
        'response'
    )

Each of the items in the ``conduit`` tuple reference a method. Each method is called in succession. This is very similar to how Django's ``MIDDLEWARE_CLASSES`` work. A conduit pipeline is specified in a ``Conduit`` view like this::

    class FormView(Conduit):
        """
        Simple view for processing form input
        """
        form_class = MyForm

        class Meta:
            conduit = (
                'deserialized_json_data',
                'validate_form',
                'process_data',
                'response'
            )

Conduit Methods
---------------

All functions in a conduit pipeline take the same four parameters as input.

#. self
    The Conduit view instance
#. request
    The Django request object
#. *args
    Capture variable number of arguments
#. **kwargs
    Capture variable number of keyword arguments

The methods also return these same values, though they may be modified in place. The only response that is different is the last, which must return a response, most likely an ``HttpResponse``.

.. warning:: The last method in a conduit must return a response, such as HttpResponse

Inheriting & Extending
----------------------

To inherit the conduit tuple from another ``Conduit`` view, your metaclass must do the inheriting. We can use a different form with the above view by inheriting its methods and conduit, while overriding its form_class::

    class OtherFormView(FormView):
        """
        Process a different form
        """
        form_class = OtherForm

        class Meta(FormView.Meta):
            pass

If you want to add or remove a step from another conduit, you must specify the new pipeline in its entirety. Here is a simple but not recommended example that extends our view from above by adding a ``publish_to_redis`` method::

    class PublishFormView(FormView):
        """
        Process a form and publish event to redis
        """
        form_class = OtherForm

        class Meta:
            conduit = (
                'deserialized_json_data',
                'validate_form',
                'process_data',
                'publish_to_redis',
                'response'
            )

In this example, we didn't inherit the meta class since we were overriding conduit anyway. 

.. warning:: Class inheritance is NOT the recommended way to customize your Conduit views.

While inheriting views, including multiple inheritance, is very familiar to Django developers, there is another more flexible way to extend your Conduit views. The methods in the conduit can reference any namespaced function, as long as they take the correct 4 input parameters.

Using namespaced methods, the recommended way to create the above view would look like this::

    class PublishFormView(Conduit):
        """
        Process a form and publish event to redis
        """
        form_class = OtherForm

        class Meta:
            conduit = (
                'myapp.views.FormView.deserialized_json_data',
                'myapp.views.FormView.validate_form',
                'myapp.views.FormView.process_data',
                'publish_to_redis',
                'myapp.views.FormView.response'
            )

The advantage here over multiple inheritance is that the source of the methods is made explicit. This makes debugging much easier if a little inconvenient.
