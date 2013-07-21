Welcome to django-conduit's documentation!
==========================================

``django-conduit`` is a RESTful API library for Django. Its primary goals are:

#. Easy to Use
#. Easy to Understand
#. Easy to Extend

Hasty Start
===========
Use this to immediately start playing around with your models in API form. Don't use in production.

#. In your main URLConf (urls.py), add the following::

    from conduit.api.utils import AutoAPI
    api = AutoAPI()

    urlpatterns = patterns('',
        ...
        url(r'^api/', include(api.urls)),
        ...
    )

#. Visit http://localhost:8000/api/v1/[yourmodelnamehere]

You're done! The AutoAPI scans your Django project for all models and exposes them via an api. 

.. warning:: DO NOT USE THIS IN PRODUCTION! It exposes all your project data.


Quick Start
===========

Django-Conduit can autogenerate your api boilerplate to get you started.

#. Install via PyPI: ``pip install django-conduit``
#. Add ``conduit`` to your ``INSTALLED_APPS``
#. Generate your API app by running the following::

    ./manage.py create_api [app1] [app2] --folder=api

Where app1 and app2 are the names of your apps

#. Point your main URLconf to your new api app::

    import api

    urlpatterns = patterns('',
        ...
        url(r'^api/', include(api.urls)),
        ...
    )

#. Visit ``localhost:8000/api/v1/[model_name]`` to fetch one of your new resources!


Next Steps
----------

* :doc:`Access & Authorization<access_authorization>`
* :doc:`Filtering & Ordering<filtering_ordering>`
* :doc:`Conduit Views<howitworks>`
* :doc:`ModelResource<api/modelresource>`
* :doc:`Customizing Resources`<api/customize>`
* :doc:`Related Resources<api/related>`




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

