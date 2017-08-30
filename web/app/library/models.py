import os

from tempfile import NamedTemporaryFile
from django.core.files import File

from belun import settings
from belun.settings import LANGUAGES_FIX_ID
from django.core.urlresolvers import reverse
from django.db import models

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from geo.models import AdminArea
from library.thumbnail import make_thumbnail
from suggest.models import logger, get_field_type
from unidecode import unidecode


class Publication(models.Model):
    """
    Represents a single published document, possibly with different languages
    """

    year = models.IntegerField(verbose_name=_('Year'), null=True, blank=True)
    name = models.TextField(verbose_name=_('name'), null=True, blank=True)
    description = models.TextField(null=True, blank=True, verbose_name=_('description'))
    pubtype = models.ForeignKey('Pubtype', verbose_name=_("Type"))

    # ---- m2m fields ----
    organization = models.ManyToManyField('nhdb.Organization', blank=True)
    author = models.ManyToManyField('Author', blank=True)
    country = models.ManyToManyField('geo.World', blank=True)
    location = models.ManyToManyField(AdminArea, blank=True)

    def __unicode__(self):
        if self.name:
            return unidecode('{}'.format(self.name))
        else:
            return str(None)

    @classmethod
    def get_translated_fields(cls, prefix='title'):
        return ['name', 'description']

    def get_absolute_url(self):
        return '/library/publication/#object=%s' % (self.id)

    def get_admin_url(self):
        return reverse("admin:%s_%s_change" %
                       (self._meta.app_label, self._meta.module_name), args=(self.id,))

    class Meta:
        verbose_name_plural = _("Publications")
        ordering = ('name',)


class Tag(models.Model):
    """
    'Keywords' or 'Tags' for a particular project
    """

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name_plural = _("Tags")
        ordering = ('name', 'name_en')


class Thumbnail(models.Model):
    # Record thumbnail locations for Version
    app_name = models.CharField(blank=True, null=True, max_length=256)
    model_name = models.CharField(blank=True, null=True, max_length=256)
    model_field = models.CharField(blank=True, null=True, max_length=256)
    model_pk = models.CharField(blank=True, null=True, max_length=256)
    resolution = models.IntegerField()
    file_name = models.CharField(blank=True, null=True, max_length=256)
    file_page = models.IntegerField(blank=True, null=True, default=0)  # Use for multipage docs like PDF files
    thumbnailPath = models.CharField(blank=True, null=True, max_length=256)

    @property
    def url(self):
        return self.thumbnailPath.replace(settings.MEDIA_ROOT, '/media/')

    @property
    def img(self):
        return mark_safe('<img src="{}">'.format(self.url))

    @classmethod
    def make(cls, instance, model_field=None, res='150', page=0, root='thumbnails', _format='jpg', rebuild=False):

        def auto_field(instance):
            """
            Return the first "FileField" or "ImageField" object
            Try to automagically guess which field if it's not provided
            :param instance:
            :return:
            """

            for fieldname in instance._meta.get_all_field_names():
                if get_field_type(instance, fieldname) in ['FileField', 'ImageField']:
                    return fieldname

        def v(fp):
            """
            Ensure uniqueness of the thumbnail file path
            """
            v = 0
            t, e = os.path.splitext(fp)
            while os.path.exists(fp):
                fp = '{}_{}{}'.format(t, v, e)
                v += 1
            return fp

        if page == 'cover':  # Saving an integer in the thumbnails table
            page = 0

        if not model_field:
            model_field = auto_field(instance)
        if not model_field:
            raise KeyError('No valid field type found for a thumbnail')

        if not hasattr(instance, model_field) and bool(getattr(instance, model_field)):
            logger.warn('Called for a Thumbnail on a nonexistant file field')
            return
        try:
            file_path = getattr(instance, model_field).path
            # workaround for UnicodeEncodeError
            file_path = file_path.encode('utf-8')

        except ValueError:
            logger.warn('Called for a Thumbnail on a  file field which returned ValueError')
            return

        if not os.path.exists(file_path):
            logger.error('Could not find model file at {}'.format(file_path))
            return False

        # Remove any instances of Thumbnail where the model is the same but the file name has changed!
        obsolete = cls.objects.filter(
            app_name=instance._meta.app_label,
            model_name=instance._meta.model_name,
            model_field=model_field,
            model_pk=instance.pk,
            resolution=res,
            # file_name=file_path,
            # file_page=page)
        ).exclude(file_name=file_path)

        thumbnail, was_created = cls.objects.get_or_create(
            app_name=instance._meta.app_label,
            model_name=instance._meta.model_name,
            model_field=model_field,
            model_pk=instance.pk,
            resolution=res,
            file_name=file_path,
            file_page=page
        )
        if not os.path.exists(file_path):
            logger.error('Could not find model file at {}'.format(file_path))

        if not was_created and thumbnail.thumbnailPath and not os.path.exists(thumbnail.thumbnailPath):
            logger.warning('Expired / removed thumbnail')

        elif rebuild is True:
            return thumbnail

        cover_file_name = "{}_{}_{}_{}_{}.{}".format(instance._meta.app_label, instance._meta.model_name, instance.pk,
                                                     res, model_field, _format)
        cover_file_dir = os.path.join(settings.MEDIA_ROOT, root, str(res))

        if not os.path.exists(cover_file_dir):
            try:
                os.makedirs(cover_file_dir)
            except:
                raise Exception('Could not create root directory at %s' % (cover_file_dir))

        thumbnail_path = os.path.join(cover_file_dir, cover_file_name)
        logger.info(thumbnail_path)
        if not (os.path.exists(thumbnail_path)) or rebuild is True:
            try:
                make_thumbnail(file_path, thumbnail_path, res, page)  # Slow
            except UnicodeEncodeError:
                pass
            except Exception as e:
                logger.exception(e.message)
                pass

            if not os.path.exists(thumbnail_path):
                thumbnail_path = '404'
            thumbnail.thumbnailPath = thumbnail_path
            thumbnail.save()
        obsolete.delete()

        return thumbnail

    @classmethod
    def get_from_instance(cls, instance):
        """
        Call this with a Django model instance to get the referenced model
        :param instance:
        :return:
        """
        if not hasattr(instance, '_meta'):
            raise TypeError('Requires a model instance')

        return cls.objects.filter(
            app_name=instance._meta.app_label,
            model_name=instance._meta.model_name,
            model_pk=instance.pk
        )

    @classmethod
    def remove(cls, instance):
        """
        Call this with a Django model instance to remove all thumbnails for this instance
        Useful to attach to a 'model delete' signal
        :param instance:
        :return:
        """
        for tn in cls.get_from_instance(instance):
            if os.path.isfile(tn.thumbnailPath):
                os.remove(tn.thumbnailPath)


class Version(models.Model):
    """
    Represents a "version" of a single published document
    This allows a single "publication" to have "versions" in different languages
    """

    def __unicode__(self):

        presentation_field = 'title'

        r = getattr(self, presentation_field)
        langs = []
        for l in self.get_translated_fields(presentation_field):

            v = getattr(self, l)

            if v is not None and v != '':
                langs.append(v)
        if langs:
            r = r + '{}'.format(','.join(langs))

        if r:
            return unidecode(r)
        else:
            return "No title"

    @classmethod
    def get_translated_fields(cls, prefix='title'):
        return ['description', 'title', 'upload', 'cover', 'url']

    @classmethod
    def populate_covers(cls, res='150'):
        """
        Populates 'thumbnail' for every Version in the system
        :return:
        """
        for version in cls.objects.all():
            version.thumbnail()

    @classmethod
    def populate_thumbnails(cls, res='150'):
        """
        Populates 'thumbnail' for every Version in the system
        :return:
        """
        for version in cls.objects.all():
            version.thumbnail_to_res()

    def thumbnail(self, language=None, **kw):
        """
        Build a thumbnail for an uploaded file
        """

        returns = {}
        for code, desc in LANGUAGES_FIX_ID:

            if language and code != language:
                continue
            if (
                not getattr(self, 'title_%s' % (code))
                and not getattr(self, 'description_%s' % (code))
            ):
                continue
            returns[code] = {}
            upload_field = 'upload_%s' % (code)
            cover_field = 'cover_%s' % (code)
            url_field = 'url_%s' % (code)

            # Move along if all language fields are empty
            # Generate an image URL (if possible)
            if (hasattr(self, cover_field) and bool(getattr(self, cover_field)) and os.path.exists(
                    getattr(self, cover_field).path)):
                try:
                    returns[code]['thumbnail'] = Thumbnail.make(self, cover_field, **kw)
                    returns[code]['image'] = returns[code]['thumbnail'].img
                except Exception as e:

                    returns[code]['image-errors'] = e.message
                    continue

            elif (hasattr(self, upload_field) and bool(getattr(self, upload_field))):

                upload = getattr(self, upload_field)
                upload_path = upload.path.encode('utf-8')
                cover = getattr(self, cover_field)

                with NamedTemporaryFile() as f:
                    # print(['convert', upload.path + '[0]', _format + ':' + f.name])
                    # subprocess.call(['convert', upload.path + '[0]', 'jpg' + ':' + f.name])
                    print(f.name)
                    logger.info('Creating thumbnail: make_thumbnail({}, {}, 600, 0)'.format(upload_path, f.name))
                    cover_file_name = os.path.split(unidecode(upload.path))[1].replace('pdf', 'jpg')
                    print(cover_file_name)
                    # raise AssertionError
                    make_thumbnail(upload_path, f.name, 600, 0)
                    cover.save(cover_file_name, File(f))

                try:
                    returns[code]['thumbnail'] = Thumbnail.make(self, upload_field, **kw)
                    returns[code]['image'] = returns[code]['thumbnail'].img
                except Exception as e:

                    returns[code]['image-errors'] = e.message
                    continue
            # Generate a link (local or foreign)

            if hasattr(self, upload_field) and bool(getattr(self, upload_field)):
                returns[code]['url'] = getattr(self, upload_field).url
            elif hasattr(self, url_field) and getattr(self, url_field) is not None:
                returns[code]['url'] = getattr(self, url_field)

            returns[code]['title'] = getattr(self, 'title_%s' % (code))
            returns[code]['description'] = getattr(self, 'description_%s' % (code))
        return returns

    def has_language(self, language_code='en',
                     language_fields=('title', 'upload', 'url', 'description')):
        """
        Returns whether or not this object has translated fields (en, pt, id, or tet)
        :return:
        """
        if language_code == 'id':
            language_code = 'ind'
        for i in language_fields:
            if getattr(self, i + '_' + language_code):
                return True
        return False

    publication = models.ForeignKey('Publication', related_name="versions")
    description = models.CharField(max_length=256, null=True, blank=True)
    title = models.CharField(max_length=256, null=True, blank=True)
    upload = models.FileField(upload_to="publications", max_length=256, null=True, blank=True)
    cover = models.FileField(upload_to="publication_covers", max_length=256, null=True, blank=True)
    url = models.CharField(max_length=256, null=True, blank=True)
    tag = models.ManyToManyField('Tag', blank=True)
    sector = models.ManyToManyField(
        'nhdb.PropertyTag', blank=True, related_name="publication_sector",
        limit_choices_to={'path__startswith': "INV."})
    activity = models.ManyToManyField(
        'nhdb.PropertyTag', blank=True, related_name="publication_activity",
        limit_choices_to={'path__startswith': "ACT."})
    beneficiary = models.ManyToManyField(
        'nhdb.PropertyTag', blank=True, related_name="publication_beneficiary",
        limit_choices_to={'path__startswith': "BEN."})

    # This additional information might not be very useful - consider moving
    # to a new location?

    journal = models.CharField(max_length=128, null=True, blank=True)
    volume = models.CharField(max_length=5, null=True, blank=True)
    issue = models.IntegerField(null=True, blank=True)
    page_start = models.IntegerField(null=True, blank=True)
    page_end = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = _("Versions")
        ordering = ('title',)


class Author(models.Model):
    name = models.CharField(max_length=128)
    displayname = models.CharField(max_length=128, null=True, blank=True)

    @classmethod
    def suggestdisplayname(cls, name):
        fn = name.split(' ')[-1]
        ini = [i[0] for i in name.split(' ')[:-1]]
        formatted_ini = '.'.join(ini) + '.'

        return "{}, {}".format(fn, formatted_ini)

    def __unicode__(self):
        return self.name

    def savesortname(self):
        self.sort_name = self.makesortname()
        self.save()

    def makedisplayname(self, initials=True):
        """
        For personal names only:
        Jackie Chan -> Chan, Jackie
        Jackie Chan -> Chan, J. (if initials)
        """
        return Author.suggestshortname(self.name)

    class Meta:
        verbose_name_plural = _("Authors")
        ordering = ('name',)


class Pubtype(models.Model):
    """
    Describes an object based on its type (eg newsletter, report...)
    """

    def __unicode__(self):
        return self.name

    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name_plural = _("Publication Types")
        ordering = ('name',)
