Forms & Validation
==================

With django-conduit you can use Django's ModelForms to easily validate your resources. You can specify a form to be used by assigning the ``form_class`` on the resource's Meta class::

    from example.forms import FooForm

    class FooResource(ModelResource):
        class Meta(ModelResource.Meta):
            form_class = FooForm

The form validation happens during POST and PUT requests. Any data sent in the request that does not correspond to the model's field names will be discarded for validation.

If errors are found during validation, they are serialized into JSON and immediately return a 400 Http response. If an error occurs while validating a related field, the JSON error is specified as having occured within that related field.