from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.safestring import mark_safe
import django_tables2 as tables
from belun import settings
from library.models import Version
from nhdb.models import PropertyTag
import modeltranslation

static_url = settings.STATIC_URL


class VersionTable(tables.Table):
    def __init__(self, *args, **kwargs):
        super(VersionTable, self).__init__(*args, **kwargs)

    class Meta:
        model = Version
        attrs = {"class": "paleblu"}


class PublicationTable(tables.Table):
    def __init__(self, *args, **kwargs):
        super(PublicationTable, self).__init__(*args, **kwargs)

    class Meta:
        # model = Publication
        attrs = {"class": "paleblu"}
        fields = ("publication", "year")

    # pk = tables.LinkColumn('library:publication:detail', args=[A('pk')])
    publication = tables.Column(empty_values=())
    year = tables.Column(empty_values=())
    organization = tables.Column()
    # pubtype = tables.Column(empty_values=())

    def render_organization(self, value):

        pattern = u'<a href="/nhdb/organization/?q=active.true#object={organization.pk}">{organization.name}({organization.orgtype_id})</a>'
        return mark_safe(
            u"<br>".join(
                [
                    pattern.format(organization=organization)
                    for organization in value.all()
                ]
            )
        )

    @property
    def language_ids(self):
        return self.context["request"].GET.getlist("language_id")

    # @property
    # def versions(self):
    #     """
    #     Build a list of Version pk's which match the search criteria so that only Versions which are relevant
    #     are displayed below the publication object in the list
    #
    #     Returns self._version, creates it if not yet created, a list or 'all'
    #     :return:
    #     """
    #     if hasattr(self, '_versions'):
    #         return self._versions
    #     request = self.context["request"]
    #     filter_terms = ("sector__path", "activity__path", "beneficiary__path", 'tag__id')
    #     filters = {}
    #     filter = False
    #     for term in filter_terms:
    #         if request.GET.getlist(term):
    #             filter=True
    #             filters[term+'__in'] = [PropertyTag.separatestring(i).upper() for i in request.GET.getlist(term)]
    #
    #     languages = Q()
    #
    #     for language_id in self.language_ids:
    #         filter = True
    #         kw = {'title_'+language_id+'__isnull': False}
    #         languages = languages | Q(**kw)
    #
    #     # If NOT filtered, we can save a lot of excess queries by including all versions
    #     if filter:
    #         self._versions = Version.objects.filter(**filters).filter(languages).values_list('pk', flat=True)
    #         return self._versions
    #     else:
    #         self._versions = 'all'
    #         return 'all'
    #
    def render_publication(self, record):

        version_count = record.versions.count()
        hide_versions_after = 5
        extra = version_count - hide_versions_after
        detail_url = "#object=" + str(record.pk)
        returns = u"<strong>{}</strong><a href={}> More &raquo;</a><br>".format(
            record.__unicode__(), detail_url
        )

        return ""
        #
        # for idx, i in enumerate(record.versions.all()):
        #     # "Filter keys" for record: "sector__path", "activity__path", "beneficiary__path"
        #     # Where there are an excessive number of version (e.g. for Blog posts), hide some rows
        #     # if self.versions != 'all' and i.pk not in self.versions:
        #     #     continue
        #
        #     if version_count > 5 and idx == hide_versions_after:
        #             returns = returns + '''<a class="btn btn-xs btn-default" data-toggle="collapse" href=".collapse-more-versions-{}" aria-expanded="false"> {} More &gt; </a>'''.format(record.pk, extra)
        #             returns = returns + '''<div class="collapse collapse-more-versions-{}">'''.format(record.pk)
        #
        #     for langcode, langname in settings.LANGUAGES_FIX_ID:
        #         if self.language_ids and langcode not in self.language_ids:
        #             continue
        #         # returns.append(u"{}".format(getattr(i, 'title_'+langcode)))
        #         title = u"{}".format(getattr(i, 'title_'+langcode))
        #         # If we're hosting this we will have a "upload_{language_code}.url" available
        #         upload = getattr(i, 'upload_'+langcode)
        #         if upload:
        #             url = upload.url
        #         # Otherwise hyperlink with url_{language_code}
        #         else:
        #             url = getattr(i, 'url_'+langcode)
        #         if not url:
        #             # Oops... We're advertising but can't deliver :(
        #             continue
        #
        #         returns = returns + u'''
        #                  <a href='{}' target='_blank'>
        #                  <img style="width:20px; height:10px; margin-right:5px;" src="{}locales/{}.png" alt="{}">{}
        #                  </a><br>'''.format(url, static_url, langcode, langname, title)
        #
        # if version_count > 5:
        #     returns = returns + '''</div>'''.format(record.pk)
        #
        # return mark_safe(returns)
