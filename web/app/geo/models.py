from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from mp_lite.mp_lite import MP_Lite


class Town(models.Model):

    SIZE_CHOICES = (
        (1, _('Major town')),
        (2, _('Minor town')),
        (3, _('Hamlet')),
    )

    geom = models.MultiPolygonField(srid=32751)
    name = models.TextField()
    size = models.IntegerField(choices=SIZE_CHOICES)


class AdminArea(MP_Lite):
    pcode = models.IntegerField(primary_key=True)
    geom = models.MultiPolygonField(srid=4326, null=True, blank=True)
    envelope = models.PolygonField(srid=4326, null=True, blank=True)
    leafletextent = models.TextField(null=True, blank=True)
    objects = models.GeoManager()

    separator = '.'
    steps = 3

    def __unicode__(self):
        return self.name

    def selectlist_repr(self):

        if 1 < self.pcode < 100:
            return u'Postu Admin. %s'%self
        elif 100 < self.pcode < 10000:
            return u'Subdistrito. %s'%self
        elif self.pcode > 10000:
            return u'Suco. %s'%self


    # class Meta:
    #     abstract = True

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains", "path__icontains",)

    @property
    def id(self):
        return self.pcode

    @property
    def geom_low_res(self):
        return self.geom.simplify(0.001)

    @property
    def envelope_geojson(self):
        return '''{
  "type": "Feature",
  "geometry": %s,
  "properties": {
    "name": "%s",
    "pcode": "%s"
  }
}'''%(self.envelope.geojson, self.name, self.pcode)


class Suco(AdminArea):

    def __unicode__(self):
        return u'Suco {}'.format(self.name)

    def selectlist_repr(self):
        return u'%s'%self

    @property
    def subdistrict(self):
        try:
            return Subdistrict.objects.get(path=self.get_ancestor_path())
        except Subdistrict.DoesNotExist:
            return None

    @property
    def district(self):
        try:
            return District.objects.get(path=self.get_ancestor_path().get_ancestor_path())
        except District.DoesNotExist:
            return None

class Subdistrict(AdminArea):
    def __unicode__(self):
        return u'Subdistrict {}'.format(self.name)

    def selectlist_repr(self):
        return u'%s'%self

    @property
    def district(self):
        try:
            return District.objects.get(path=self.get_ancestor_path())
        except District.DoesNotExist:
            return None

class District(AdminArea):
    def __unicode__(self):
        return u'Postu Admin. {}'.format(self.name)

    def selectlist_repr(self):
        return u'%s'%self


class Road(models.Model):
    geom = models.MultiLineStringField(srid=32751)
    osm_id = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=255, null=True)
    highway = models.CharField(max_length=255, null=True)
    route = models.CharField(max_length=255, null=True)

    def __unicode__(self):
        return self.name


class World(models.Model):

    '''
    Countries of the world, not simplified, in EPSG:4326
    '''


    class Meta:
        ordering = ['name']

    iso3 = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    geom = models.MultiPolygonField(srid=4326, null=True, blank=True)
    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains", "iso3__icontains",)


class Worldsimple(models.Model):

    '''
    Countries of the world, simpified, in EPSG:4326
    '''
    iso3 = models.CharField(max_length=3)
    name = models.CharField(max_length=100)
    geom = models.PolygonField(srid=4326)
    objects = models.GeoManager()

    def __unicode(self):
        return self.name


class PlaceAlternate(models.Model):

    '''
    Alternative or "unofficial" place names which are commonly used
    but not officially recognised in 2010 census information
    '''
    name = models.CharField(max_length=100)
    geom = models.MultiPolygonField(srid=32751)
    objects = models.GeoManager()

    def __unicode__(self):
        return self.name
