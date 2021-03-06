from django.contrib.contenttypes.models import ContentType
from django.db import models

try:
    from django.contrib.contenttypes.generic import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.fields import GenericForeignKey

class CustomField(models.Field):
    def __init__(self, *args, **kwargs):
        super(CustomField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'customfield'


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
    custom_field = CustomField()


class Item(models.Model):
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
