from django import template
from nhdb.models import *
from django.db.models import Q, Count


from django import template


def filter_from_params(req, objects, targetfields=None):
    '''
    Filter a set by parameters passed by the URL string
    Allows including or excluding objects based on GET params
    targetfields : dictionary of {GET parameter: , {'filter': field, 'table': Table}}
    objects: set of Model objects

    targetfields = {
        'ben':{'field':'targetbeneficiaries__id','table':TargetBeneficiaries},
        'org':{'field':'project_organization__organization_id','table':Organization},
        'inv':{'field':'involvementareas__id','table':AreaOfInvolvement},
        'act':{'field':'mainactivities__id','table':MainActivity},
        'dis':{'field':'project_projectaddress__pk','table':PlaceCode
        }
    '''

    if targetfields == None:
        targetfields = {
            'ben': {'field': 'targetbeneficiaries__id', 'table': TargetBeneficiaries},
            'org': {'field': 'project_organization__organization_id', 'table': Organization},
            'inv': {'field': 'involvementareas__id', 'table': AreaOfInvolvement},
            'act': {'field': 'mainactivities__id', 'table': MainActivity},
            'place': {'field': 'project_projectaddress__pk', 'table': PlaceCode}
        }

    def _g(param):
        _return = req.GET.getlist(param)
        print(_return)
        if _return == ['']:
            _return = []
        return _return

    def qrangefilter(d, fieldname, bucket=10000):
        '''Return Q object where a field is within a given range'''
        sr, er = int(d) * bucket, int(d) * bucket + bucket - 1
        return Q(**{fieldname: (sr, er)})

    def districthandler(objects):
        '''
        Filter by district (based on the value of the PlaceCode 
        which references district, SD and suco)
        '''
        filtering = []
        param = 'district'
        if param not in list(req.GET.keys()):
            return None
        # 'Include Districts' filter

        q_obj = Q()
        for d in _g(param):
            q_obj |= qrangefilter(d, 'projectaddress__place__range')
            opts = {'name': PlaceCode.objects.get(pk=d).name, 'table': 'PlaceCode'}
            filtering.append({'class': 'filtertext include', 'param': 'x_' + param, 'name': 'Filter to include only where {0[table]} is {0[name]}'.format(opts)})
        objects = objects.filter(q_obj)

        # 'Exclude Districts' filter
        q_obj = Q()
        for d in _g('x_' + param):
            opts = {'name': PlaceCode.objects.get(pk=d).name, 'table': 'PlaceCode'}
            filtering.append({'class': 'filtertext exclude', 'param': 'x_' + param, 'name': 'Filter to exclude where {0[table]} is {0[name]}'.format(opts)})
            q_obj |= qrangefilter(d, 'projectaddress__place__range')
        objects = objects.exclude(q_obj)

        return objects, filtering

    def standardpkhandler(objects):
        '''
        Most of the time we'll filter by primary key
        '''

        _filtering = []

        for param in list(targetfields.keys()):

            if param not in list(req.GET.keys()):
                continue

            q_obj = Q()
            param_name = targetfields[param]
            if param_name['field'].endswith('_id'):
                for value in _g(param):
                    newq = Q(**{param_name['field']: value})
                    q_obj |= newq
                    print(newq)
                    opts = {'name': param_name['table'].objects.get(pk=value), 'table': param_name['table'].objects.get(pk=value)._meta.verbose_name.capitalize()}
                    _filtering.append({'class': 'filtertext include', 'param': param, 'name': 'Filter to only include where {0[table]} is {0[name]}'.format(opts)})

                objects = objects.filter(q_obj)

        # 'Except' any of the above with 'x_' in front of param name
        for param in list(targetfields.keys()):
            q_obj = Q()
            param_name = targetfields[param]
            if param_name['field'].endswith('_id'):
                if _g('x_' + param) != []:

                    if 'x_' + param not in list(req.GET.keys()):
                        continue

                    for value in _g('x_' + param):
                        q_obj |= Q(**{param_name['field']: value})
                        opts = {'name': param_name['table'].objects.get(pk=value), 'table': param_name['table'].objects.get(pk=value)._meta.verbose_name.capitalize()}
                        _filtering.append({'class': 'filtertext exclude', 'param': 'x_' + param, 'name': 'Filter to exclude where {0[table]} is {0[name]}'.format(opts)})
                    objects = objects.exclude(q_obj)

        return objects, _filtering

    def orgtypefilter(objects):
        '''
        Returns a filter to include or exclude
        based on an org type code 
        in the request
        '''
        _filtering = []

        q_obj = Q()
        for value in _g('otype'):
            q_obj |= Q(orgtype=value)
            opts = {'name': value, 'table': 'Organization'}
            _filtering.append({'class': 'filtertext include', 'name': 'Filter to only include where {0[table]} is an {0[name]}'.format(opts)})
        objects = objects.filter(q_obj)

        q_obj = Q()
        for value in _g('x_otype'):
            q_obj |= Q(orgtype=value)
            opts = {'name': value, 'table': 'Organization'}
            _filtering.append({'class': 'filtertext exclude', 'name': 'Filter to only include where {0[table]} is not an {0[name]}'.format(opts)})
        objects = objects.exclude(q_obj)

        return objects, _filtering

    def orgnamelike(objects):
        q_obj = Q()
        for value in _g('orgname'):
            q_obj |= Q(name__icontains=value)
            print(q_obj)
            opts = {'name': value, 'table': 'Organization'}
            _filtering.append({'class': 'filtertext include', 'name': 'Filter to only include where {0[table]} name is like {0[name]}'.format(opts)})
        objects = objects.filter(q_obj)
        return objects, _filtering

    def projnamelike(objects):
        q_obj = Q()
        for value in _g('projname'):
            q_obj |= Q(name__icontains=value)
            print(q_obj)
            opts = {'name': value, 'table': 'Project'}
            _filtering.append({'class': 'filtertext include', 'name': 'Filter to only include where {0[table]} name is like {0[name]}'.format(opts)})
        objects = objects.filter(q_obj)
        return objects, _filtering

    params = req.GET.copy()
    g = params.get

    filtering = []
    objects, _filtering = standardpkhandler(objects)
    filtering.extend(_filtering)

    if _g('orgname'):
        objects, _filtering = orgnamelike(objects)
        filtering.extend(_filtering)

    if _g('projname'):
        objects, _filtering = projnamelike(objects)
        filtering.extend(_filtering)

    if _g('otype') or _g('x_otype'):
        objects, _filtering = orgtypefilter(objects)
        filtering.extend(_filtering)

    if _g('district') or _g('x_district'):
        objects, _filtering = districthandler(objects)
        filtering.extend(_filtering)

    return objects, filtering


def filterbycount(q, field, annotation_name='count', lt=None, gt=None):
    '''Annotate the queryset , filter byt lt or gt, and return filtered
    model'''
    assert isinstance(field, str)
    kw = {annotation_name: Count(field)}
    q = q.annotate(**kw)
    print(q.count())
    if gt:
        kw_gt = {'%s__%s' % (annotation_name, 'gt'): gt}
        q = q.filter(**kw_gt)
    if lt:
        kw_lt = {'%s__%s' % (annotation_name, 'lt'): lt}
        q = q.filter(**kw_lt)

    print(kw)
    #~ print kw_lt
    print(kw_gt)

    print(q.count())
    return q
