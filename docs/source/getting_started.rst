Getting Started
===============

Installation
------------

#. Install via PyPI: ``pip install django-conduit``
#. Add the following to your INSTALLED_APPS::
    
    INSTALLED_APPS = (
        ...
        'conduit',
        ...
    )

Create Your API
---------------

We're going to use the AutoAPI to automatically set up the boilerplate for all your Conduit resources!

#. Generate your API app by running the following::

    ./manage.py create_api [app1 app2 app3] --folder=api

#. Add the 'api' Django app to your INSTALLED_APPS::
    
    INSTALLED_APPS = (
        ...
        'api',
        ...
    )

#. Add the API to your root urls.py::

    urlpatterns = patterns('',
        ...
        url(r'^api/', include('api.urls')),
        ...
    )

Using Your API
--------------

#. Visit ``localhost:8000/api/v1/[model_name]`` to fetch one of your new resources!