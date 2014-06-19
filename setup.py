#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

excludes = ['docs', 'example']

packages = [
    'conduit',
    'conduit.api',
    'conduit.test',
    'conduit.management',
    'conduit.management.commands',
]

install_requires = [
        'python_dateutil >= 2.1',
        'six >= 1.3.0'
]

try:
    import importlib
except ImportError:
    install_requires.append('importlib')

setup(
    name='django-conduit',
    version='0.1.1',
    description='Easy and powerful REST APIs for Django.',
    author='Alec Koumjian',
    author_email='akoumjian@gmail.com',
    url='https://github.com/akoumjian/django-conduit',
    packages=packages,
    package_dir={'conduit': 'conduit'},
    include_package_data=True,
    install_requires=install_requires,
    zip_safe=False,
    license='Apache 2.0',
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
