import json

import warnings
from django.db.models import Q
from django.apps import apps

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from geo.models import District, Subdistrict, Suco, AdminArea
from nhdb.models import Project
get_model = apps.get_model

def index(request):
    return render(request, 'geo/index.html')


def map(request):

    context = {}
    context['Districts'] = District.objects.all()
    context['Subdistricts'] = Subdistrict.objects.all()
    context['Sucos'] = Suco.objects.all()

    return render(request, 'geo/map.html', context)


def projectplace(request, project_pk):
    pcodes = [p.place.pcode for p in Project.objects.get(pk=project_pk).projectplace_set.all()]
    places = AdminArea.objects.filter(pcode__in=pcodes)
    return render(request, 'geo/adminareas.json', {'places': places}, content_type='application/json')


def projectplace_intersect_convex_hull(request,project_pk):

    # Fast, small geometries formed from the union of the convex hull of the geometries

    project = Project.objects.get(pk=project_pk)
    projectplaces = [p for p in project.projectplace_set.all()]
    places_list = projectplaces.values_list('place', flat=True)

    AdminArea.objects.filter(pcode__in = places_list).aggregate(Union('geom'))['geom__union'].convex_hull
    AdminArea.objects.filter(pcode__in = places_list).envelope()


def _placeenvelopes(request):

    returns = {}
    for a in AdminArea.objects.all():
        envelope = a.geom.extent
        envelope = [round(i,3) for i in envelope]
        e = [ [envelope[1], envelope[0]], [envelope[3], envelope[0]], [envelope[3], envelope[2]], [envelope[1], envelope[2]], [envelope[1], envelope[0]] ]
        returns[a.pcode] = e

    return HttpResponse(json.dumps(returns, indent=1), content_type='application/json')


@cache_page(60 * 15)
def placeenvelopes(request):

    returns = ['{ "type": "FeatureCollection", "features": [']
    for i in AdminArea.objects.all():
        returns.append(i.envelope_geojson)
        returns.append(',')
    returns.pop(-1) #  Get rid of last ','
    returns.append(']}')
    return HttpResponse(returns, content_type='application/json')


def placeconvexhulls(request):

    returns = {}
    for a in AdminArea.objects.all():
        returns[a.pcode] = [(round(i[1],3),round(i[0],3)) for i in a.geom.convex_hull.simplify(0.005).coords[0]]

    return HttpResponse(json.dumps(returns), content_type='application/json')


def places(request):
    '''
    Returns the AdminAreas covered by pcode / path
    :param request:
    :return:
    '''
    pcodes = request.GET.getlist('pcode')

    if pcodes == []:
        pcodes = [1,2,3,101,401,50101]

    places = AdminArea.objects.filter(pcode__in=pcodes)

    return render(request, 'geo/adminareas.json', {'places': places}, content_type='application/json')


def search(request, model="adminarea", languages='en'):
    """
    Returns matching objects for a select2.js list
    :param request:
    :param model:
    :return:

    Additional GET parameters: 'fields' and 'search'
    """

    if isinstance(model, str):
        model = get_model('geo', model)
        assert hasattr(model, 'objects'), 'Please pass a model instance or name to this function'

    model_field_names = model._meta.get_all_field_names()

    fields = request.GET.getlist('fields', ['name'])
    search_term = request.GET.get('search', 'baucau')

    q = Q()
    kweries = {}
    for field_name in fields:
        if field_name not in model_field_names:
            raise NameError('There is no field called %s in the model %s' % (field_name, model._meta.verbose_name))
        kweries[field_name + '__icontains'] = search_term
        kwery = {field_name + '__icontains': search_term}
        q = q | Q(**kwery)

    filtered = model.objects.filter(q)
    if filtered.count() == 0:
        warnings.warn('Nothing found')
        raise TypeError(filtered.query.sql_with_params())

    items = []
    for i in filtered:

        item = {'pk': i.pk}
        for fieldname in fields:
            item[fieldname] = getattr(i, fieldname)
        items.append(item)

    return HttpResponse(json.dumps({'returns': items}), content_type='application/json')