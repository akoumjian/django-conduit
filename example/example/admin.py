from django.contrib import admin

from example.models import Foo, Bar, Baz


admin.site.register(Foo)
admin.site.register(Bar)
admin.site.register(Baz)
