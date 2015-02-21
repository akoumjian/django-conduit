from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

class Bar(models.Model):
    name = models.CharField(max_length=250)


class Baz(models.Model):
    name = models.CharField(max_length=250)


class Foo(models.Model):
    name = models.CharField(max_length=250)
    text = models.TextField()
    integer = models.IntegerField()
    float_field = models.FloatField()
    boolean = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    birthday = models.DateField(auto_now_add=True)
    decimal = models.DecimalField(max_digits=5, decimal_places=2)
    file_field = models.FileField(upload_to='test')
    bar = models.ForeignKey(Bar, null=True)
    bazzes = models.ManyToManyField(Baz)


class Item(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
