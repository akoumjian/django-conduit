#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(
    name='django-conduit',
    version='0.1.0',
    description='Easy and powerful REST APIs for Django.',
    author='Alec Koumjian',
    author_email='akoumjian@gmail.com',
    url='https://github.com/akoumjian/django-conduit',
    packages=[
        'conduit',
    ],
    requires=[
        'mimeparse',
        'dateutil(>=1.5, !=2.0)',
    ],
    install_requires=[
        'python_dateutil >= 2.1',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)