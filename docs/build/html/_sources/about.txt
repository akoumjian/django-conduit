About
=====

Django-Conduit is meant to accomodate the most common API patterns such as dealing with related resources and permissions access. It was designed to be very easy to read, debug, and extend, and ultimately make your code more readable as well.

The conduit based views are aimed to respect and take advantage of the request-response cycle. This includes ideas such as transaction support, minimizing database queries, but most importantly a pipeline of events which can be easily intercepted, extended, and introspected.

We believe Django-Conduit is the fastest way to develop a REST API that works like you would expect or want it to.

Why not Django-REST-Framework?
------------------------------

DRF was built around Django's Class Based Views and as a result produces highly cryptic yet verbose view classes. Interacting with CBVs often involves using special class methods that hopefully hook into the right part of the request-response cycle. Class based inheritance makes a very frustrating experience when developing complex views.


Why not Django-Tastypie?
------------------------

Django-Conduit is heavily inspired by Tastypie. It uses a similar declarative syntax for resources, as well as a similar syntax for related fields and metaclasses. Conduit was partly built to simplify and streamline a lot of Tastypie's internal logic. While built rather differently, Conduit aims to emulate some of Tastypie's best features.