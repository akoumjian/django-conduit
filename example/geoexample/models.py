from django.contrib.gis.db import models as geomodels

class GeoBar(geomodels.Model):
    name = geomodels.CharField(max_length=250)
    geom = geomodels.GeometryField( srid=4326 ) # the default srid, but listed here to be explicit
    # required manager
    objects = geomodels.GeoManager()

    class Meta:
        app_label = 'geoexample'


class GeoBaz(geomodels.Model):
    name = geomodels.CharField(max_length=250)
    geom = geomodels.GeometryField( srid=4326 ) # the default srid, but listed here to be explicit
    # required manager
    objects = geomodels.GeoManager()

    class Meta:
        app_label = 'geoexample'



class GeoFoo(geomodels.Model):
    geom = geomodels.GeometryField( srid=4326 ) # the default srid, but listed here to be explicit
    name = geomodels.CharField(max_length=250)
    text = geomodels.TextField()
    integer = geomodels.IntegerField()
    float_field = geomodels.FloatField()
    boolean = geomodels.BooleanField()
    created = geomodels.DateTimeField(auto_now_add=True)
    birthday = geomodels.DateField(auto_now_add=True)
    decimal = geomodels.DecimalField(max_digits=5, decimal_places=2)
    file_field = geomodels.FileField(upload_to='test')
    bar = geomodels.ForeignKey(GeoBar, null=True)
    bazzes = geomodels.ManyToManyField(GeoBaz)
    # required manager
    objects = geomodels.GeoManager()

    class Meta:
        app_label = 'geoexample'





