import django_filters
from django.apps import apps
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django_filters.filterset import BaseFilterSet
from django_tables2 import SingleTableView
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from library import serializers
from forms import *
from nhdb.models import Organization
from suggest.models import Suggest, AffectedInstance
from tables import VersionTable


def index(request):
    return render(request, 'library/index.html')


def thumbnail(request, app_name, model_name, pk, res=150):
    try:
        t = Thumbnail.make(instance=apps.get_model(app_name, model_name).objects.get(pk=pk), res=int(res))
    except:
        return HttpResponseNotFound()
    return HttpResponse(mark_safe(t.img))


def publicationlist(request):
    # Prefetching some links speeds up rendering time - greatly!
    prefetch = ['versions', 'pubtype', 'organization', 'author']

    if request.GET.get('tag__id'):
        prefetch.append('versions__tag')
    if request.GET.get('sector__path'):
        prefetch.append('versions__sector')
    if request.GET.get('activity__path'):
        prefetch.append('versions__activity')
    if request.GET.get('beneficiary__path'):
        prefetch.append('versions__beneficiary')

    logger.info(prefetch)

    def object_list(request, prefetch=('versions', 'sectors', 'tags', 'pubtype', 'organization')):
        objects = Publication.objects.all().prefetch_related(*prefetch)
        GET = request.GET
        filters = {}
        params = ('org', 'pubtype')
        version_params = ('tag__id',)
        version_filter_terms = ("sector__path", "activity__path", "beneficiary__path")

        for param in version_params:
            if GET.getlist(param):
                filters['versions__' + param + '__in'] = GET.getlist(param)

        for param in params:
            if GET.getlist(param):
                # Rewrite shorthand requests here
                if param == 'org':
                    _param = 'organization'
                else:
                    _param = param
                filters[_param + '__in'] = GET.getlist(param)

        years = GET.getlist('year')
        if years:
            param = 'year'
            if len(years) == 1:
                filters[param + '__in'] = GET.getlist(param)
            elif len(years) >= 2:
                filters[param + '__gte'] = min([int(i) for i in GET.getlist(param)])
                filters[param + '__lte'] = max([int(i) for i in GET.getlist(param)])

        for term in version_filter_terms:
            if GET.getlist(term):
                filters["versions__" + term + '__in'] = [PropertyTag.separatestring(i).upper() for i in
                                                         request.GET.getlist(term)]

        languages = Q()
        language_ids = GET.getlist('language_id')
        for language_id in language_ids:
            kw = {'versions__title_' + language_id + '__isnull': False,
                  'versions__title_' + language_id + '__icontains': ' '}
            languages = languages | Q(**kw)
        try:

            objects = objects.filter(**filters).filter(languages).distinct()

        except ValueError as e:
            raise

        text = GET.get('q.text') or GET.get('text')
        if text:
            q = Q()
            for lang, lang_name in LANGUAGES_FIX_ID:
                for fieldname in ['name', 'description', 'versions__description', 'versions__title']:
                    k = {fieldname + '_' + lang + '__icontains': text}
                    q = q | Q(**k)
            # raise AssertionError, q
            objects = objects.filter(q)

        primarysource = request.GET.get('primarysource') or 'false'

        if primarysource == 'false':  # Default
            objects = objects.exclude(pubtype='PRI')
        if primarysource == 'true':
            pass
        if primarysource == 'only':
            objects = objects.filter(pubtype='PRI')

        return objects

    def dashboard(publications=None):
        if publications is None:
            publications = Publication.objects.all()
        dashboard = {}
        from collections import Counter
        publications = publications.prefetch_related('tag', 'sector', 'author', 'org')

        tags = list(publications.values_list('tag__name', flat=True))
        organizations = publications.values_list('organization__name', flat=True)
        sectors = publications.values_list('sector__name', flat=True)
        authors = publications.values_list('author__name', flat=True)

        dashboard[_('Tag')] = dict(Counter(tags))
        dashboard[_('Organization')] = dict(Counter(organizations))
        dashboard[_('Sector')] = dict(Counter(sectors))
        dashboard[_('Author')] = dict(Counter(authors))
        return dashboard

    context = {
        'lang': request.LANGUAGE_CODE,
        'filters': {
            'language_id': [{'value': s[0], 'label': s[1]} for s in settings.LANGUAGES_FIX_ID],
            'tag__id': Tag.objects.all(),
            'sector__path': PropertyTag.objects.filter(path__startswith='INV.'),
            'pubtype': [{'value': p.pk, 'label': p.name} for p in Pubtype.objects.exclude(code='PRI')],
            'org': [{'value': o.pk, 'label': u'{}'.format(o.name)} for o in Organization.objects.annotate(
                num_publications=Count('publication')).filter(num_publications__gt=0)],
        },
        'activefilters': {}
    }

    for f in context['filters'].keys():
        if request.GET.getlist(f) != []:
            context['activefilters'][f] = request.GET.getlist(f)

        context['activefilters']['primarysource'] = request.GET.get('primarysource') or 'false'

    context['object_class_count'] = Publication.objects.count()

    context['object_list'] = object_list(request, prefetch)
    context['dashboard'] = dashboard(context['object_list'])

    return render(request, 'library/publication_list.html', context)


def project_table_excel(request):
    pass


def version_thumbnail_nginx(request):
    '''
    NGINX is set up to forward a request for "thumbnail does not exist"
    :param request:
    :return:
    '''
    # Example request:
    # https://localhost/nhdb/thumbnail/?request=/media/publication_pages/150/en/07-057r7_Web_Map_Tile_Service_Standard_PRBxiHh_Stpcw2r_1.jpg

    r = request.GET.get('request')

    x, root, d, res, lang, filename = r.split('/')

    #    ['',
    # 'media',
    # 'publication_pages',
    # '150',
    # 'en',
    # '07-057r7_Web_Map_Tile_Service_Standard_PRBxiHh_Stpcw2r_1.jpg']

    if d == "publication_pages":

        page = int(filename.split('_')[-1][:-4])  # Cut off the last underscore + digit (page number)
        filename = filename[0:-1 * (len(filename.split('_')[-1])) - 1]

        kw = {'upload_{}__icontains'.format(lang): filename}

        version = Version.objects.filter(**kw).first()
        # t = Version.objects.filter(**kw).first().thumbnail_to_res(language=lang)

        if not version:
            return HttpResponseNotFound(open('/webapps/project/media/404.jpg').read(), content_type='image/jpg')
        t = version.page_image(page=page, language=lang, res=res)
        return HttpResponse(open(t).read(), content_type='image/jpg')

    elif d == "publication_covers":

        filename = filename[0:-1 * (len(filename.split('_')[-1])) - 1]

        kw = {'cover_{}__icontains'.format(lang): filename}

        version = Version.objects.filter(**kw).first()
        # t = Version.objects.filter(**kw).first().thumbnail_to_res(language=lang)

        if not version:
            return HttpResponseNotFound(open('/webapps/project/media/404.jpg').read(), content_type='image/jpg')
        t = version.page_image(language=lang, res=res, root="/webapps/project/media/publication_covers/", page="cover")
        return HttpResponse(open(t).read(), content_type='image/jpg')


def version_thumbnail(request, version_pk, language='en'):
    '''
    Returns URL for a version thumbnail, creates it if nonexistant;
    Intended to reduce waiting times for big Publications
    :param request:
    :param version_pk:
    :return:
    '''
    _g = request.GET.get
    kw = {
        'res': _g('res', 150),
        '_format': _g('format', 'jpg')
    }

    if kw['_format'] not in ('jpg', 'png', 'gif', 'jpeg', 'pdf'):
        kw['_format'] = 'jpg'

    try:
        kw['res'] = int(kw['res'])
        if kw['res'] < 150:
            kw['res'] = 150
        elif kw['res'] > 1000:
            kw['res'] = 1000
    except ValueError:
        kw['res'] = 150

    try:
        v = Version.objects.get(pk=version_pk)
        t = v.thumbnail(language=language, **kw)
        if t.get('image-errors'):
            raise AssertionError('Could not generate thumbnail: %s' % t['image-errors'])
        thumbnail = t[language]['thumbnail']
        return HttpResponse(open(thumbnail.thumbnailPath).read(), content_type='image/' + kw['_format'])

    except:
        raise


def version_page(request, pk, page, language):
    version = Version.objects.get(pk=pk)
    res = request.GET.get('size', 150)
    p = version.page_image(page=page, language=language, res=res)
    return HttpResponse(open(p).read(), content_type='image/jpg')


def suggested_publication(request, suggestion_pk):
    context = {}
    context['suggestion'] = Suggest.objects.get(pk=suggestion_pk)

    return render(request, 'library/suggested_publication.html', context)


class PublicationDetail(DetailView):
    model = Publication


def publicationdashboard(request):
    context = {}

    try:
        context['suggestion'] = Suggest.objects.get(pk=request.GET.get('suggestion'))
    except:
        context['suggestion'] = request.GET.get('suggestion')

    try:
        context['publication'] = Publication.objects.get(pk=request.GET.get('publication'))
    except:
        context['publication'] = request.GET.get('publication')

    return render(request, 'library/publication_dashboard.html', context)


def form(request, model, form='main'):
    app_name = 'library'

    from django.apps import apps

    g = request.GET.get
    args = {}
    models = apps.get_app_config(app_name).models
    for m_name in models:
        m = models[m_name]

        if g(m_name):
            args[m_name] = m.objects.get(pk=g(m_name))

        if g('_' + m_name):
            args[m_name] = Suggest.objects.get(pk=g('_' + m_name))

    from . import forms, forms_delete

    f = None
    p = request.GET.get

    template = 'nhdb/crispy_form.html'

    if form == 'main':
        f_name = '%sForm' % model.title()
    elif form == 'delete':
        f_name = '%s%sForm' % (model.title(), 'Delete')
        if hasattr(forms_delete, f_name):
            f = getattr(forms_delete, f_name)
            return render(request, template, {'form': f(**args)})
    else:
        f_name = '%s%sForm' % (model.title(), form.title())
    if hasattr(forms, f_name):
        f = getattr(forms, f_name)
        return render(request, template, {'form': f(**args)})

    if settings.DEBUG:
        raise NotImplementedError("Class nhdb.forms.{} is not defined yet".format(f_name))

    return HttpResponseBadRequest(
        mark_safe("<form>Class nhdb.forms.{} is not defined yet</form>".format(f_name)))


def suggested_publications(request):
    '''
    List of suggested additions: enrty point to create a new pub or modify an existing one (ie add / change version,
    organization, author etc)
    :param request:
    :return:
    '''
    context = {}
    context['suggestions'] = Suggest.objects.filter(
        affectedinstance__in=AffectedInstance.objects.filter(primary=True, model_name='library_publication'),
        action="CM")
    return render(request, 'library/suggested_publications.html', context)


class AuthorCreate(CreateView):
    model = Author


class PublicationDelete(DeleteView):
    model = Publication


class VersionDetail(DetailView):
    model = Version

    def get_context_data(self, **kwargs):
        context = super(VersionDetail, self).get_context_data(**kwargs)

        context['version_language'] = []
        languagecodes = [c[0] for c in LANGUAGES_FIX_ID]

        for lc in languagecodes:
            if not self.object.has_language(lc):
                continue

            upload = getattr(self.object, 'upload_%s' % lc)

            context['version_language'].append({
                'languagecode': lc,
                'upload': upload,
                'upload_exists': os.path.exists(upload.path),
                'url': getattr(self.object, 'url_%s' % lc),
                'cover': getattr(self.object, 'cover_%s' % lc),
                'title': getattr(self.object, 'title_%s' % lc),
                'description': getattr(self.object, 'description_%s' % lc)
            })
        return context


class VersionDelete(DeleteView):
    model = Version


class VersionUpdate(UpdateView):
    model = Version
    form_class = VersionUpdateForm


class VersionList(SingleTableView):
    model = Version
    table_class = VersionTable


class OrganizationInFilter(django_filters.rest_framework.FilterSet):
    organization = django_filters.ModelMultipleChoiceFilter(
        name="organization__id",
        to_field_name="id",
        queryset=Organization.objects.all()
    )

    class Meta:
        model = Publication
        fields = ('name', 'pubtype', 'author', 'sector', 'tag')


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = serializers.PublicationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    ordering_fields = ('name', 'year')
    # filter_fields = ('name', 'pubtype', 'author', 'organization__id__in', 'sector', 'tag')
    filter_class = OrganizationInFilter

    def get_queryset(self):
        queryset = Publication.objects.all()
        queryset = queryset.prefetch_related(
            'author', 'organization', 'sector', 'tag'
        )
        return queryset
