Django-Conduit
==============

Easy and powerful REST APIs for Django.

Why Use Django-Conduit?
-----------------------

- Easy to read, easy to debug, easy to extend
- Smart and efficient :doc:`Related Resources<related>`


See the :doc:`full list of features<features>`.

Table of Contents
=================
.. toctree::
   :maxdepth: 2

   filtering_ordering
   related
   access_authorization
   forms_validation
   conduit
   about

Getting Started
===============

Django-Conduit will automatically create your starting api based on your existing models.

#. Install via PyPI: ``pip install django-conduit``
#. Add the following to your INSTALLED_APPS::
    
    INSTALLED_APPS = (
        ...
        'conduit',
        # 'api',
    )

#. Generate your API app by running the following::

    ./manage.py create_api [name_of_your_app] --folder=api

#. Uncomment 'api' in your INSTALLED_APPS
#. Point your main URLconf (normally project_name/urls.py) to your new 'api' app::

    import api

    urlpatterns = patterns('',
        ...
        url(r'^api/', include(api.urls)),
        ...
    )

#. Visit ``localhost:8000/api/v1/[model_name]`` to fetch one of your new resources!

All your new resources will be defined in api/views.py, and they will be registered with your Api object in api/urls.py.




Topics
------

* :doc:`Filtering & Ordering<filtering_ordering>`
* :doc:`Related Resources<related>`
* :doc:`Access & Authorization<access_authorization>`
* :doc:`Forms & Validation<forms_validation>`
* :doc:`Conduit Views<conduit>`
* :doc:`ModelResource<api/modelresource>`
* :doc:`Customizing Resources`<api/customize>`




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

