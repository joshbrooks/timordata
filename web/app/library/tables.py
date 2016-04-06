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
        fields = ('publication', 'year', 'organizations')

    # pk = tables.LinkColumn('library:publication:detail', args=[A('pk')])
    publication = tables.Column(empty_values=())
    year = tables.Column(empty_values=())
    organizations = tables.Column(empty_values=())
    pubtype = tables.Column(empty_values=())

    def render_organizations(self,record):

        def format_parameters(organization):
            return [
                reverse('nhdb:organization:detail', kwargs={'pk':organization.pk}),
                organization.name]

        format_string = u'''<a href={0}>{1}</a>'''
        try:
            organizations = [format_string.format(*format_parameters(i)) for i in record.organization.all()]
        except:
            raise

        return mark_safe('<br>'.join(organizations))

    def render_publication(self, record):
        request = self.context["request"]

        filter_terms = ("sector__path", "activity__path", "beneficiary__path", 'tag__id')
        filters = {}
        for term in filter_terms:
            if request.GET.getlist(term):
                filters[term+'__in'] = [PropertyTag.separatestring(i).upper() for i in request.GET.getlist(term)]

        detail_url = '#object='+str(record.pk)

        returns = u'<strong>{}</strong><a href={}> More &raquo;</a><br>'\
            .format(record.__unicode__(), detail_url)
        versions = record.versions.filter(**filters)

        languages = Q()
        language_ids = request.GET.getlist('language_id')
        for language_id in language_ids:
            kw = {'title_'+language_id+'__isnull': False}
            languages = languages | Q(**kw)

        versions.filter(languages)

        version_count = versions.count()
        hide_versions_after = 5
        extra = version_count - hide_versions_after

        for idx, i in enumerate(versions):
            # "Filter keys" for record: "sector__path", "activity__path", "beneficiary__path"
            # Where there are an excessive number of version (e.g. for Blog posts), hide some rows
            if version_count > 5 and idx == hide_versions_after:
                    returns = returns + '''<a class="btn btn-xs btn-default" data-toggle="collapse" href=".collapse-more-versions-{}" aria-expanded="false"> {} More &gt; </a>'''.format(record.pk, extra)
                    returns = returns + '''<div class="collapse collapse-more-versions-{}">'''.format(record.pk)


            for langcode, langname in settings.LANGUAGES_FIX_ID:
                if language_ids and langcode not in language_ids:
                    continue
                # returns.append(u"{}".format(getattr(i, 'title_'+langcode)))
                title = u"{}".format(getattr(i, 'title_'+langcode))
                # If we're hosting this we will have a "upload_{language_code}.url" available
                upload = getattr(i, 'upload_'+langcode)
                if upload:
                    url = upload.url
                # Otherwise hyperlink with url_{language_code}
                else:
                    url = getattr(i, 'url_'+langcode)
                if not url:
                    # Oops... We're advertising but can't deliver :(
                    continue

                returns = returns + u'''
                         <a href='{}' target='_blank'>
                         <img style="width:20px; height:10px; margin-right:5px;" src="{}locales/{}.png" alt="{}">{}
                         </a><br>'''.format(url, static_url, langcode, langname, title)

        if version_count > 5:
            returns = returns + '''</div>'''.format(record.pk)

        return mark_safe(returns)
