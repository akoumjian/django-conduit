Welcome to django-conduit's documentation!
==========================================

``django-conduit`` is a RESTful API library for Django. Its primary goals are:

#. Easy to Use
#. Easy to Understand
#. Easy to Extend

Hasty Start
===========

.. warning:: DO NOT USE THIS IN PRODUCTION! It exposes all your project data.

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


Quick Start
===========

Django-Conduit can automatically create an api app for you based on your existing models!

#. Install via PyPI: ``pip install django-conduit``
#. Add the following to your INSTALLED_APPS::
    
    INSTALLED_APPS = (
        ...
        'conduit',
        # 'api',
    )

Note that we leave the api app commented out for now.

#. Generate your API app by running the following::

    ./manage.py create_api [app1] [app2] --folder=api

Where app1 and app2 are the names of the apps you want included in your API.

#. Uncomment 'api' in your INSTALLED_APPS
#. Point your main URLconf to your new api app::

    import api

    urlpatterns = patterns('',
        ...
        url(r'^api/', include(api.urls)),
        ...
    )

#. Visit ``localhost:8000/api/v1/[model_name]`` to fetch one of your new resources!


Topics
------

* :doc:`Filtering & Ordering<filtering_ordering>`
* :doc:`Related Resources<api/related>`
* :doc:`Access & Authorization<access_authorization>`
* :doc:`Forms & Validation<forms_validation>`
* :doc:`Conduit Views<howitworks>`
* :doc:`ModelResource<api/modelresource>`
* :doc:`Customizing Resources`<api/customize>`




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

