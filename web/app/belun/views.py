import json
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib.flatpages.models import FlatPage
from django.http.response import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, render_to_response
from django.contrib.auth import logout
from django.template import Context
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django_tables2 import SingleTableView
from settings import LANGUAGES_FIX_ID
from suggest.models import Suggest

language_codes = [i[0] for i in LANGUAGES_FIX_ID]
def index(request):
    # return HttpResponse('ok')
    if request.GET.get('background') == '2':
        return render(request, 'index_background_2.html')

    if request.GET.get('background') == '3':
        return render(request, 'index_background_3.html')

    return render(request, 'index.html')


def indexmanifest(request):

    content_type = "text/cache-manifest"
    manifest = [
        "CACHE MANIFEST",
        "/static/timordata.css",
        "/static/font-awesome.min.css",
        "/static/bootstrap-modal/css/bootstrap-modal-bs3patch.css",
        "/static/bootstrap/css/bootstrap.min.css",
        "/static/timordata.css",
        "/static/jquery.js",
        "/static/bootstrap/js/bootstrap.js",
        "/static/backgrounds/background_min.jpg"]


    return HttpResponse('\n'.join(manifest), content_type=content_type)


def about(request):
    if request.LANGUAGE_CODE == 'tet':
        return render(request, 'about_tet.html')

    return render(request, 'about.html')


def history(request):
    return render(request, 'history.html')

def selecttwo(request, app_name='library', model_name='tag', filter_field='name', filter_param='icontains', create=False):

    '''
    Returns a list (formatted for select2) of filtered options
    :param request:
    :param app_name: Application name
    :param model_name:  Model name - Optionally with '_detail'
    :param filter_field:
    :param filter_param:
    :return:

    Specify a property named 'selectlist_repr' on a model to modify the appearance of the object in the list

    '''

    m = apps.get_model('{}.{}'.format(app_name, model_name))
    q = request.GET.get('q') or request.GET.get('q')
    k = {}

    filter_name = '{}__{}'.format(filter_field, filter_param)

    k[filter_name] = q
    try:
        qs = m.objects.filter(**k)
    except ValueError:
        qs = m.objects.none()

    _list = []

    if create:
        exact_filter = {}
        exact_filter_name = '{}__{}'.format(filter_field, 'iexact')
        exact_filter[exact_filter_name] = q
        if qs.filter(**exact_filter).count() != 1:
            _list.append({'id':'__new__{}'.format(q),'text':'(New {}) {}'.format(model_name,q)})

    for r in qs:

        if hasattr(r, 'selectlist_repr'):
            text = getattr(r, 'selectlist_repr')
            if callable(text):
                text = text()

        else:
            text = getattr(r, filter_field)

        _list.append({
            'id': getattr(r, 'pk'),
            'text': text
        })

    response = {"results": _list}

    return HttpResponse(json.dumps(response), content_type='application/json')


def chosen(request, app_name='library', model_name='tag', filter_field='name', filter_param='icontains', include_suggestions=False):

    '''
    Returns a list (formatted for select2) of filtered options
    :param request:
    :param app_name: Application name
    :param model_name:  Model name - Optionally with '_detail'
    :param filter_field:
    :param filter_param:
    :return:

    Specify a property named 'selectlist_repr' on a model to modify the appearance of the object in the list


    '''

    m = apps.get_model('{}.{}'.format(app_name, model_name))
    q = request.GET.get('data[q]')
    k = {}

    filter_name = '{}__{}'.format(filter_field, filter_param)

    k[filter_name] = q
    try:
        qs = m.objects.filter(**k)
    except ValueError:
        qs = m.objects.none()

    _list = []

    for r in qs:

        if hasattr(r, 'selectlist_repr'):
            text = getattr(r, 'selectlist_repr')
        else:
            text = getattr(r, filter_field)

        _list.append({
            'id': getattr(r, 'pk'),
            'text': text
        })

    response = {"q":q, 'results': _list}

    # If include_suggestions is TRUE, add in any matching values from the Suggestions application

    if include_suggestions:
        suggestion_model_name = '{}_{}'.format(app_name, model_name)
        suggestions = Suggest.objects.filter(affectedinstance__primary = True, affectedinstance__model_name = suggestion_model_name, action='CM')
        _suggest_list = []

        for r in suggestions:

            if hasattr(r, 'selectlist_repr'):
                text = getattr(r, 'selectlist_repr')
            else:
                text = getattr(r, filter_field)

            _list.append({
                'id': getattr(r, 'pk'),
                'text': text
            })

    return HttpResponse(json.dumps(response), content_type='application/json')


def selecttwo_create(request, **kw):
    kw['create'] = True
    return selecttwo(request, **kw)



class TranslatedPageList(list):
    def __init__(self, language, **kwargs):

        super(TranslatedPageList, self).__init__(**kwargs)
        self.language = language

# @login_required
def flatpagelist(request):
    """
    Edit a flatpage by primary key
    :param pk:
    :return:
    """
    c = {}

    def pages():
        """
        Return a list of pages and translated languages
        """
        page_objects = FlatPage.objects.all()
        pages = {}

        pages['languages'] = language_codes
        pages['translated'] = {}

        page_names =  [page.url.split('/')[1] for page in page_objects]

        for page in page_objects:
            page_name = page.url.split('/')[1]
            if page_name not in pages['translated']:
                pages['translated'][page_name] = TranslatedPageList(size = len(language_codes))

            language = page.url.split('/')[-2]

            if language == '':
                language = 'en' # Default to english
            if language not in language_codes:
                language = 'en' # Default to english
                #raise AssertionError, language

            language_index = pages['languages'].index(language)
            pages['translated'][page_name][language_index] = page

        return pages
    c['pages'] = pages()

    return render(request, 'flatpages/flatpage_list.html', c)

def flatpage(request, pk):
    return HttpResponse('Not here yet! pk %s'%pk)



@method_decorator(login_required, name='dispatch')
class FlatpageList(ListView):
    model = FlatPage


@method_decorator(login_required, name='dispatch')
class FlatpageDetail(DetailView):
    model = FlatPage
