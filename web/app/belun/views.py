import json
from django.apps import apps
from django.http.response import HttpResponse
from django.shortcuts import render, get_object_or_404

from django.contrib.auth import logout
from suggest.models import Suggest


def logout_view(request):
    logout(request)
    return render(request, 'index.html')

def index(request):
    # return HttpResponse('ok')
    if request.GET.get('background') == '2':
        return render(request, 'index_background_2.html')

    if request.GET.get('background') == '3':
        return render(request, 'index_background_3.html')

    return render(request, 'index.html')


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
