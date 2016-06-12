# from django.contrib.gis.db import models
from datetime import datetime
from belun import settings
from django.apps import apps

from geo.models import Suco
from pivottable import pivot_table as pivot
from django.contrib.gis.db import models
from django.db.models import Q
from mp_lite import MP_Lite
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
import json
from library.models import Thumbnail
import logging
logger = logging.getLogger(__name__)
from unidecode import unidecode

__all__ = [
    'Organization', 'Person',
    'ProjectOrganizationClass',
    'ProjectType', 'RecordOwner', 'Project', 'ProjectImage',
    'ProjectOrganization', 'ProjectPerson', 'ProjectPlace',
    'OrganizationPlace', 'OrganizationClass',
    'PropertyTag', 'ProjectStatus', 'ExcelDownloadFeedback'
]


def unisafe(inputstring):
    try:
        return u'{}'.format(inputstring)
    except UnicodeEncodeError:
        try:
            return unidecode(inputstring)
        except:
            return 'Sorry, unicode error'


class ProjectManager(models.Manager):
    def past_enddate(self):
        """
        Projects which are active but the end date has already finished
        :return:
        """
        return super(ProjectManager, self) \
            .get_queryset() \
            .filter(status__pk='A') \
            .filter(enddate__lt=datetime.today().date())

    def active(self, include_unknown=False):
        """
        Return projects which are 'active' and have an enddate which is greater than today
        """
        q = Q(enddate__gte=datetime.today().date())
        if include_unknown:
            q = q | Q(enddate__isnull=True)

        return super(ProjectManager, self) \
            .get_queryset() \
            .filter(status__pk='A') \
            .filter(q)

    def inactive(self):
        return super(ProjectManager, self) \
            .get_queryset() \
            .exclude(status__pk='A')

    def active_or_unknown(self):
        """
        Return projects which may or may not be active. This includes null end dates.
        """
        return self.active(include_unknown=True)


class OrganizationManager(models.Manager):
    def invalid_emails(self):
        return super(OrganizationManager, self) \
            .get_queryset() \
            .exclude(email__regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9]+\.[a-zA-Z0-9.+-]+$") \
            .exclude(email__isnull=True)

    def no_email(self):
        return super(OrganizationManager, self) \
            .get_queryset() \
            .filter(email__isnull=True)

    def valid_email(self):
        return super(OrganizationManager, self) \
            .get_queryset() \
            .filter(email__regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9]+\.[a-zA-Z0-9.]+$")


class ExcelDownloadFeedback(models.Model):
    PURPOSE_CHOICES = (
        ('PP', 'Project planning'),
        ('RE', 'Research'),
        ('IN', 'Personal interest'),
        ('OT', 'Other (please specify)'),
    )

    name = models.CharField(_('name'), max_length=150)
    organization = models.CharField(_('organization'), max_length=150)
    description = models.TextField(_('description'), null=True, blank=True)
    email = models.EmailField(_('email'), null=True, blank=True)
    purpose = models.CharField(max_length=2, choices=PURPOSE_CHOICES, )
    purposeother = models.CharField(_('Other purpose'), max_length=150, null=True, blank=True)
    referralurl = models.CharField(max_length=256, null=True, blank=True)


class Organization(models.Model):
    name = models.CharField(_('name'), max_length=150)
    description = models.TextField(_('description'), null=True, blank=True)
    orgtype = models.ForeignKey('OrganizationClass', verbose_name=_('class'), default="LNGO", )
    active = models.BooleanField(default=True)
    fongtilid = models.IntegerField(null=True, blank=True, verbose_name="Org. ID (Fongtil)")
    justiceid = models.IntegerField(null=True, blank=True, verbose_name="Org. ID (Min. Justice)")
    stafffulltime = models.IntegerField(null=True, blank=True, verbose_name="Full time staff")
    staffparttime = models.IntegerField(null=True, blank=True, verbose_name="Part time staff")
    verified = models.DateField(null=True, blank=True, auto_now=True)
    phoneprimary = models.CharField(max_length=64, null=True, blank=True, verbose_name="Phone")
    phonesecondary = models.CharField(max_length=64, null=True, blank=True, verbose_name="Alternate phone")
    email = models.CharField(max_length=128, null=True, blank=True)
    fax = models.CharField(max_length=64, null=True, blank=True)
    web = models.CharField(max_length=64, null=True, blank=True)
    facebook = models.CharField(max_length=64, null=True, blank=True)


    @property

    @property
    def encryptedemail(self):
        e = Email(self.email)
        return e.rot

    @property
    def filecounts(self):
        filecounts = {}
        for lang in settings.LANGUAGES_FIX_ID:
            key = 'upload_' + lang[0]
            kw = {key: ''}
            version_model = apps.get_model('library', 'version')
            count = version_model.objects.filter(publication__organization=self).exclude(**kw).count()
            if count > 0:
                filecounts[lang[0]] = count
        return filecounts

    @property
    def initialsetbounds(self):
        '''
        Returns a JSON string which can be injected into template to instruct leaflet to pan/zoom to the organization's
        location(s)
        :return:
        '''

        default_zoom = 13
        places = self.organizationplace_set

        e = places.collect().extent
        sw = [e[1], e[0]]
        ne = [e[3], e[2]]

        if sw == ne:
            sw[0] = sw[0] - 0.05
            sw[1] = sw[1] - 0.05
            ne[0] = ne[0] + 0.05
            ne[1] = ne[1] + 0.05

        return json.dumps((sw, ne))

    class Meta:
        ordering = ['name', ]

    def __unicode__(self):
        return unisafe(self.name)

    def get_absolute_url(self):
        return "/nhdb/organization/?q=active.true#object=%s" % (self.pk)

    def get_admin_url(self):
        return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.module_name), args=(self.id,))

    @property
    def featurecollection(self):

        return json.dumps({'type': "FeatureCollection",
                           'features': [project.feature for project in self.project_set.all()]
                           })

        # objects = OrganizationManager


class OrganizationClass(models.Model):
    def __unicode__(self):
        return unicode(self.orgtype)

    code = models.CharField('Code', max_length=5, primary_key=True)
    orgtype = models.CharField('Type', max_length=150)


import re


class Email(object):
    def __init__(self, address):
        self._address = address
        if not address:
            self.address, self.domain = ['', '']

        elif '@' not in address:
            self.address, self.domain = ['', '']
        try:
            self.address, self.domain = address.split('@')
            self.address = re.sub('\.', ' dot ', self.address).encode('rot13')
            self.domain = re.sub('\.', ' dot ', self.domain).encode('rot13')
        except:
            self.address, self.domain = None, None

    @property
    def rot(self):
        # Reversed, rot13 encoded, substitution of '.' and '@'
        if self._address:
            e = re.sub('\.', ' dot ', self._address)
            e = re.sub('@', ' at ', e)
            return e[::-1].encode('rot13')


def emailencode(email):
    """
    Reversed, rot13 encoded address with substitution of '.' and '@'
    :param email:
    :return:

    This javascript code will reverse the process

    String.prototype.reverse = function () {return this.split("").reverse().join("");};
    String.prototype.dotat = function () {return this.replace(/ at /gi, '@').replace(/ dot /gi ,'.')};
    String.prototype.rot13 = function () {return this.replace(/[a-zA-Z]/gi, function (c) {return String.fromCharCode(
        (c <= "Z" ? 90 : 122) >= (c = c.charCodeAt(0) + 13) ? c : c - 26);});};
    $(document).ready(function(){
        $('button.showliame').on('click', function(){
            var table = $('.email').parents('table:first')
            var index = $('.email').parent().children().index( $('.email') )
            $(this).addClass('disabled')
            table.find('tbody tr').each(function(){
                var i = $(this).children('td')[index];
                $(i).css({color:'green'});
                $(i).text($(i).text().reverse().rot13().dotat())
            })
        });
    });
    """

    reverse_code_obfuscated = """var _0x7972=["\x72\x65\x76\x65\x72\x73\x65","\x70\x72\x6F\x74\x6F\x74\x79\x70\x65","","\x6A\x6F\x69\x6E","\x73\x70\x6C\x69\x74","\x64\x6F\x74\x61\x74","\x2E","\x72\x65\x70\x6C\x61\x63\x65","\x40","\x72\x6F\x74\x31\x33","\x5A","\x63\x68\x61\x72\x43\x6F\x64\x65\x41\x74","\x66\x72\x6F\x6D\x43\x68\x61\x72\x43\x6F\x64\x65","\x63\x6C\x69\x63\x6B","\x74\x61\x62\x6C\x65\x3A\x66\x69\x72\x73\x74","\x70\x61\x72\x65\x6E\x74\x73","\x2E\x65\x6D\x61\x69\x6C","\x69\x6E\x64\x65\x78","\x63\x68\x69\x6C\x64\x72\x65\x6E","\x70\x61\x72\x65\x6E\x74","\x64\x69\x73\x61\x62\x6C\x65\x64","\x61\x64\x64\x43\x6C\x61\x73\x73","\x74\x64","\x67\x72\x65\x65\x6E","\x63\x73\x73","\x74\x65\x78\x74","\x65\x61\x63\x68","\x74\x62\x6F\x64\x79\x20\x74\x72","\x66\x69\x6E\x64","\x6F\x6E","\x62\x75\x74\x74\x6F\x6E\x2E\x73\x68\x6F\x77\x6C\x69\x61\x6D\x65","\x72\x65\x61\x64\x79"];String[_0x7972[1]][_0x7972[0]]=function(){return this[_0x7972[4]](_0x7972[2])[_0x7972[0]]()[_0x7972[3]](_0x7972[2])};String[_0x7972[1]][_0x7972[5]]=function(){return this[_0x7972[7]](/ at /gi,_0x7972[8])[_0x7972[7]](/ dot /gi,_0x7972[6])};String[_0x7972[1]][_0x7972[9]]=function(){return this[_0x7972[7]](/[a-zA-Z]/gi,function(_0xf065x1){return String[_0x7972[12]]((_0xf065x1<=_0x7972[10]?90:122)>=(_0xf065x1=_0xf065x1[_0x7972[11]](0)+13)?_0xf065x1:_0xf065x1-26)})};$(document)[_0x7972[31]](function(){$(_0x7972[30])[_0x7972[29]](_0x7972[13],function(){var _0xf065x2=$(_0x7972[16])[_0x7972[15]](_0x7972[14]);var _0xf065x3=$(_0x7972[16])[_0x7972[19]]()[_0x7972[18]]()[_0x7972[17]]($(_0x7972[16]));$(this)[_0x7972[21]](_0x7972[20]);_0xf065x2[_0x7972[28]](_0x7972[27])[_0x7972[26]](function(){var _0xf065x4=$(this)[_0x7972[18]](_0x7972[22])[_0xf065x3];$(_0xf065x4)[_0x7972[24]]({color:_0x7972[23]});$(_0xf065x4)[_0x7972[25]]($(_0xf065x4)[_0x7972[25]]()[_0x7972[0]]()[_0x7972[9]]()[_0x7972[5]]());});})});"""

    if email:
        if '@' in email:
            e = re.sub('\.', ' dot ', email)
            e = re.sub('@', ' at ', e)
            return e[::-1].encode('rot13')


class Person(models.Model):
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return unicode(self.name)

    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, null=True, blank=True)
    organization = models.ForeignKey('nhdb.Organization', null=True, blank=True)
    phone = models.CharField(max_length=64, null=True, blank=True)
    email = models.CharField(max_length=64, null=True, blank=True)
    verified = models.DateField(auto_now=True, null=True, blank=True)

    @property
    def email_rot(self):
        return Email(self.email)

    @property
    def selectlist_repr(self):

        try:
            organization = self.organization
        except:
            organization = ''

        return '{} - {} at {}'.format(self.name, self.title, organization)

    def get_absolute_url(self):
        if not self.pk:
            return None
        return reverse('nhdb:person:detail', kwargs={'pk': self.pk})


class PropertyTag(MP_Lite):
    def __unicode__(self):
        return unicode(self.name)

    # class Meta:
    #     ordering = ["description"]

    steps = 3

    @property
    def get_absolute_url(self):
        return reverse('nhdb:propertytag:list')

    description = models.CharField(max_length=255)


class ProjectType(models.Model):
    def __unicode__(self):
        return unicode(self.description)

    description = models.CharField(max_length=255)


class RecordOwner(models.Model):
    def __unicode__(self):
        return unicode(self.description)

    description = models.CharField(max_length=255)


class ProjectImage(models.Model):
    def __unicode__(self):
        try:
            if self.project:
                return u'Image from project {} - {}'.format(unicode(self.project), unicode(self.description))
            else:
                return None
        except Exception, e:
            return e.message

    description = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='projectimage/%Y%m%d/', null=True, blank=True)
    project = models.ForeignKey('Project')

    def thumbnail(self, res=150):
        try:
            return Thumbnail.make(self, model_field='image', res=res)
        except KeyError:
            pass
        except Exception, e:
            logger.error('Failed to create thumbnail: {}'.format(e.message))
            return False

    @property
    def thumbnailurl(self):
        if self.thumbnail():
            return self.thumbnail().url

    @property
    def thumbnailurl_large(self):
        if self.thumbnail(res=600):
            return self.thumbnail(res=600).url

    @property
    def thumbnailurl_tiny(self):
        if self.thumbnail(res=50):
            return self.thumbnail(res=50).url


class Project(models.Model):
    def __unicode__(self):

        # Translated fields : should automagically do whichever 'name' is first on the list
        if self.name:
            return unicode(self.name)
        return '?'

    class Meta:
        ordering = ['name', ]

    name = models.CharField(_('name'), max_length=256, blank=True, null=True)
    description = models.TextField(null=True, blank=True, verbose_name=_("Project Description"))
    startdate = models.DateField(null=True, blank=True, verbose_name="Start date")
    enddate = models.DateField(null=True, blank=True, verbose_name="End date")
    verified = models.DateField(auto_now=True, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    status = models.ForeignKey('ProjectStatus', null=True, verbose_name="Status", default='A')
    projecttype = models.ForeignKey('ProjectType', null=True, blank=True)

    person = models.ManyToManyField(Person, through='ProjectPerson', blank=True)
    # properties = models.ManyToManyField('PropertyTag', null=True, blank=True, )
    # Deprecated (again!) in favour of individual fields
    sector = models.ManyToManyField(
            'nhdb.PropertyTag', blank=True, related_name="project_sector",
            limit_choices_to={'path__startswith': "INV."})
    activity = models.ManyToManyField(
            'nhdb.PropertyTag', blank=True, related_name="project_activity",
            limit_choices_to={'path__startswith': "ACT."})
    beneficiary = models.ManyToManyField(
            'nhdb.PropertyTag', blank=True, related_name="project_beneficiary",
            limit_choices_to={'path__startswith': "BEN."})

    place = models.ManyToManyField("geo.AdminArea", through='ProjectPlace', blank=True)
    organization = models.ManyToManyField(Organization, through='ProjectOrganization', blank=True)
    stafffulltime = models.IntegerField(null=True, blank=True, verbose_name=_('Full time staff'))
    staffparttime = models.IntegerField(null=True, blank=True, verbose_name=_('Part time staff'))

    objects = ProjectManager()

    @property
    def has_locations(self):
        return self.projectplace_set.count() > 0

    def get_admin_url(self):
        return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.module_name), args=(self.id,))

    def get_absolute_url(self):
        # return reverse('nhdb:project:detail', kwargs={'pk': self.pk})
        return reverse('nhdb:project:list') + '?q=status.A#object=%s' % self.pk

    def image_overlay_url(self):
        '''
        Connect to an external WMS service to get an image of the project locations
        :return:
        '''
        pcodes = self.projectplace_set.values_list('place_id', flat=True)
        pcodes = pcodes or ['none']

        return '/wms/?pcode={}'.format(','.join([str(i) for i in pcodes]))

        # return '/wms/?pcode={}'.format(','.join([str(i) for i in pcodes]))

    @property
    def past_enddate(self):
        """
        Projects which are active but the end date has already finished
        :return:
        """
        if not self.enddate:
            return False

        if self.enddate < datetime.today().date() and self.status.code == 'A':
            return True

    @property
    def coordinates(self):

        return [p.coordinates for p in self.projectplace_set.all()]

    @property
    def feature(self):

        properties = {
            'name': self.name,
            'id': self.pk,
        }

        f = {"type": "Feature",
             "geometry": {
                 "type": "MultiPolygon",
                 "coordinates": self.coordinates,
             },
             "properties": properties
             }

        return f

    @property
    def geojson(self):
        return json.dumps(self.feature)

    @classmethod
    def pivot_table(cls, _filter, field_name, relation_data=None):
        return pivot(cls, _filter, field_name, relation_data=None)


class ProjectStatus(models.Model):
    def __unicode__(self):
        return self.description

    code = models.CharField(max_length=2, primary_key=True)
    description = models.CharField(max_length=256)


class ProjectOrganization(models.Model):
    def __unicode__(self):
        try:
            return self.organization.__unicode__() + unicode(" ") + self.project.__unicode__()
        except AttributeError:
            return 'Invalid project / organization'

    class Meta:
        verbose_name = "Project to Organization link"
        unique_together = (('project', 'organization'))

    project = models.ForeignKey('Project')
    organization = models.ForeignKey(Organization, null=True, blank=True)
    organizationclass = models.ForeignKey('ProjectOrganizationClass', default='P',
                                          verbose_name=_('Organization involvement'))
    notes = models.CharField(max_length=256, null=True, blank=True, verbose_name=_('Notes about this relationship'))


class ProjectOrganizationClass(models.Model):
    """
    Replaces an "option" for organizationclass
    """
    code = models.CharField(max_length=3, primary_key=True)
    description = models.TextField()

    def __unicode__(self):
        return self.description


class ProjectPerson(models.Model):
    class Meta:
        unique_together = (('person', 'project'))

    def __unicode__(self):

        if not self.pk:
            return 'A new link between a project and a person'

        try:

            if self.is_primary:
                return u'{} as primary contact of {}'.format(self.person, self.project)
            return u'{} as contact of {}'.format(self.person, self.project)

        except Exception, e:
            try:

                return u'contact of {}'.format(self.project)

            except Exception, e:

                return 'Error in formatting: {}'.format(e.message)

    project = models.ForeignKey(Project)
    person = models.ForeignKey(Person)
    is_primary = models.BooleanField(default=False)
    verified = models.DateField(auto_now=True, null=True, blank=True)


class ProjectPlace(models.Model):
    def __unicode__(self):
        if self.description:
            return self.description
        elif self.place.name:
            return u'{}, {}'.format(
                    self.project.name, self.place.name)
        else:
            return '?'

    class Meta:
        unique_together = (("project", "place"))

    project = models.ForeignKey(Project)
    place = models.ForeignKey("geo.AdminArea")
    description = models.CharField(max_length=256, null=True, blank=True)

    objects = models.GeoManager()

    @property
    def json(self):
        return self.place.geom.convex_hull.json

    def _coordinates(self, convex_hull=False, envelope=False):
        if envelope:
            return json.loads(self.place.geom.envelope.json)['coordinates']

        if convex_hull:
            return json.loads(self.place.geom.convex_hull.json)['coordinates']

        return json.loads(self.place.geom.json)['coordinates']

    @property
    def coordinates(self):
        return self._coordinates(envelope=True)
        # return self._coordinates()

    @property
    def feature(self):

        properties = {
            'description': self.description,
            'id': self.pk,
        }

        f = {"type": "Feature",
             "geometry": {
                 "type": "Point",
                 "coordinates": self.coordinates,
             },
             "properties": properties
             }

        return f


class OrganizationPlaceDescription(models.Model):
    """
    Cache the OrganizationPlace to prevent looking up suco, subd., district every time
    """

    def __unicode__(self):
        return '{} {} {}'.format(self.suco, self.subdistrict, self.district)

    organizationplace = models.OneToOneField('nhdb.OrganizationPlace', primary_key=True)
    suco = models.CharField(max_length=256, null=True, blank=True)
    subdistrict = models.CharField(max_length=256, null=True, blank=True)
    district = models.CharField(max_length=256, null=True, blank=True)


class OrganizationPlace(models.Model):
    def __unicode__(self):

        if self.description:
            return self.description
        elif self.organization and self.point:
            return u'Office or location for {}'.format(self.organization)

    organization = models.ForeignKey('nhdb.Organization', null=True, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)
    point = models.PointField(srid=4326, null=True)
    phone = models.CharField(max_length=256, null=True, blank=True)
    email = models.CharField(max_length=256, null=True, blank=True)

    objects = models.GeoManager()

    def update_place(self):

        description, created = OrganizationPlaceDescription.objects.get_or_create(organizationplace = self)
        try:
            suco = Suco.objects.get(geom__contains=self.point)
        except Suco.DoesNotExist:
            return
        if description.suco == suco.name:
            logger.debug('skip updating info for {}'.format(self))
            return
        description.suco = suco.name
        description.subdistrict = suco.subdistrict.name
        description.district = suco.subdistrict.district.name
        description.save()
        logger.debug('updated info for {}'.format(self))


    @property
    def location(self):
        """
        Returns the admin areas (district, subdistrict, suco) of this point
        :return:
        """
        return {
            'district': apps.get_model('geo', 'district').objects.filter(geom__contains=self.point).first() or 'None',
            'subdistrict': apps.get_model('geo', 'subdistrict').objects.filter(
                geom__contains=self.point).first() or 'None',
            'suco': apps.get_model('geo', 'suco').objects.filter(geom__contains=self.point).first() or 'None',
        }

    @property
    def locationstring(self):
        l = self.location
        return '{}, {}, {}'.format(l['suco'], l['subdistrict'], l['district'])

    @property
    def lat(self):
        return self.point.y

    @property
    def lng(self):

        return self.point.x

    @property
    def latlng(self):
        """
        Getting tired of remembering if "x = lat" or "y = lat"!
        :return:
        """

        return [self.lat, self.lng]

    @property
    def latlngjs(self):
        return json.dumps(self.latlng)

    @property
    def feature(self):

        if self.point:
            coordinates = [self.point.x, self.point.y]
        else:
            coordinates = None

        properties = {
            'description': self.description,
            'phone': self.phone,
            'email': self.email,
            'id': self.pk,
            'organization': self.organization_id
        }

        f = {"type": "Feature",
             "geometry": {
                 "type": "Point",
                 "coordinates": coordinates,
             },
             "properties": properties
             }

        return f

    @classmethod
    def organization_place_feature_collection(cls, _filter, as_list=False):

        queryset = cls.objects.filter(**_filter)
        if as_list is False:
            featurecollection = {"type": "FeatureCollection", 'features': []}
            for i in queryset:
                featurecollection['features'].append(i.feature)
            return json.dumps(featurecollection)

        return json.dumps([i.feature for i in queryset])
