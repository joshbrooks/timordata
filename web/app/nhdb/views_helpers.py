from belun import settings
from nhdb.models import *
from django.db.models import Q
import datetime
from geo.models import AdminArea
from itertools import product


def fromiso(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()

def intize(l):
    """
    Filter a list returning only integers and strings which can
    be coerced to integers
    """

    def getint(e):
        """
        Return an integer if an integer or string which can be 
        coerced to int is passed
        """
        if isinstance(e, int):
            return e
        if e.isdigit():
            return int(e)
        else:
            return None

    if 'all' in l:
        return []

    return [i for i in map(getint, l) if i is not None]


def orgset_filter(rq, qs=Organization.objects.all()):
    """
    Filter organization by GET request
    """

    projects = Project.objects.all()

    orgtype = rq.GET.getlist('orgtype', None)
    namelike = rq.GET.get('name', None)
    status = rq.GET.get('status', "active")

    # Also possible to set "inactive=on"
    if rq.GET.get('inactive') == 'on':
        status='any'

    place = rq.GET.getlist('place', None)
    pcode = rq.GET.getlist('pcode', None)

    # "tags" and "projectstatus" actually refer to project not organization.
    # That distinction is made here.

    tags = rq.GET.getlist('tag', [])
    tags.extend(rq.GET.getlist('inv', []))
    tags.extend(rq.GET.getlist('ben', []))
    tags.extend(rq.GET.getlist('act', []))

    projectstatus = rq.GET.getlist('projectstatus', 'any')
    projectplace = rq.GET.getlist('location')

    if orgtype:
        if orgtype != 'any':
            qs = qs.filter(orgtype__pk__in=orgtype)

    if projectplace:
        projects = projects.filter(projectplace__place__pcode__in=projectplace)

    if projectstatus:
        if 'any' not in projectstatus:
            projects = projects.filter(status__in=projectstatus)

    if tags:
        # tags = [PropertyTag.getfromstring(i) for i in tags]
        # Treat tags differently, by "grouping"
        # This is what used to happen:
        # qs = qs.filter(project__properties__in = tags)
        # WHERE beneficiary = 'Children' OR beneficiary = 'Community' OR sector='WASH' OR sector = 'fishing'
        # New behaviour is like this
        # WHERE (beneficiary = 'Children' OR beneficiary = 'Community') AND (sector='WASH' OR sector = 'fishing')
        filters = {}

        for tag in tags:
            root_name = tag[:3].upper()
            if root_name not in filters:
                filters[root_name] = []
            filters[root_name].append(PropertyTag.separatestring(tag).upper())

        for root_name, child_tags in filters.items():
            lookup = {'act': 'activity', 'ben': 'beneficiary', 'inv': 'sector'}
            _filter = {
                lookup[root_name.lower()] + '__path__in': [PropertyTag.separatestring(v).upper() for v in child_tags]}

            projects = projects.filter(**_filter)

    # There are two ways to determine "place": using the "pcode" or 
    # using the place path. Internally "pcode" is converted to "path".

    if pcode:
        place = set(place).union(set([i[0] for i in AdminArea.objects.filter(pk__in=pcode).values_list('path')]))

    if place or pcode:

        q = Q()
        for path in place:
            q = q | Q(place__path__istartswith=path)

        projects = projects.filter(q)

    projects = projects.distinct()
    if projects.count() != Project.objects.count():
        qs = qs.filter(project__in=projects)
    if namelike:
        qs = qs.filter(name__icontains=namelike)

    if status:
        if status == "inactive":
            qs = qs.filter(active=False)
        if status == "active":
            qs = qs.filter(active=True)
        if status == "any":
            pass

    organizations = qs.distinct()

    if projects:
        projects = projects.filter(organization__in=organizations)

    return organizations, projects


def projectset_filter(
        rq,
        pl=Project.objects.all(),
        pass_parameters=('orgs', 'csrfmiddlewaretoken', 'searchtexttext', 'display', 'type', 'search', 'page', 'sort',
                         'format', 'nullenddate', 'nullstartdate')):
    """
    Filter projects by foreign key properties based on request GET
    parameters
    """

    def translatedfilter(parameters, filter_values, filter_type="icontains"):

        # For compatibility with "django-modeltranslation" expand a nonspecific filter such as "name" to "name_en",
        # "name_pt" etc
        _q = Q()
        for language, parameter, value in product(settings.LANGUAGES_FIX_ID, parameters, filter_values):
            filter_name = '%s_%s__%s' % (parameter, language[0], filter_type)
            __filter = {filter_name: value}
            _q = _q | Q(**__filter)

        return _q

    params = rq.GET.iterlists()
    translated_fields = ('name', 'description')

    for i in params:
        # opt is the GET parameter eg 'place' or 'inv'
        # vals is a list of values eg['10','15']

        opt, vals = i
        if opt in pass_parameters or vals == [''] or vals == ['all']:
            continue

        if opt in translated_fields:

            values = []
            for v in vals:
                values.extend([i.strip() for i in v.split(',')])

            pl = pl.filter(translatedfilter(parameters=translated_fields, filter_values=values))

        elif opt == 'place':
            q = Q()
            # Get the places
            for v in vals:
                q = q | Q(place__path__startswith=v)
            pl = pl.filter(q)
            print pl

        elif opt == 'status':
            pl = pl.filter(status_id__in=vals)

        elif opt == 'organization':
            q = Q()
            for v in vals:
                q = Q(organization__pk=v)
            pl = pl.filter(q)

        elif opt == 'pcode':
            q = Q()
            for v in intize(vals):
                q = Q(place=AdminArea.objects.get(pk=v))
                q = q | Q(place__in=AdminArea.objects.get(pk=v).get_descendants())
            pl = pl.filter(q)

        elif opt == 'projectstatus':
            q = Q()
            for v in vals:
                q = q | Q(status=v)
            pl = pl.filter(q)

        # INV, BEN, ACT rationalization (Sept 2014)
        # Legacy code
        elif opt.upper() in [i[0] for i in PropertyTag.get_root_nodes().values_list('path')]:
            lookup = {'act': 'activity', 'ben': 'beneficiary', 'inv': 'sector'}

            _filter = {lookup[opt.lower()]+'__path__in': [PropertyTag.separatestring(v).upper() for v in vals]}
            pl = pl.filter(**_filter)

        elif opt == 'orgtype':
            q = Q()
            for v in vals:
                q = q | Q(organization__orgtype__code=v)
            pl = pl.filter(q)

        elif opt == 'startdateafter':
            if rq.GET.get('nullstartdate') == 'on':
                q = Q(startdate__gt=fromiso(vals[0])) | Q(startdate=None)
                pl = pl.filter(q)
            else:
                pl = pl.filter(startdate__gt=fromiso(vals[0]))
        elif opt == 'startdatebefore':
            pl = pl.filter(startdate__lt=fromiso(vals[0]))
        elif opt == 'enddateafter':
            # if rq.GET.get('nullenddate') == 'on':
            q = Q(enddate__gt=fromiso(vals[0])) | Q(enddate=None)
            pl = pl.filter(q)
            # else:
            # pl = pl.filter(enddate__gt = fromiso(vals[0]))
            pass
            #  pl = pl.filter(enddate__gt = fromiso(vals[0]))
        elif opt == 'enddatebefore':
            pl = pl.filter(startdate__lt=fromiso(vals[0]))

        else:
            raise AssertionError('Invalid filter passed: %s' % opt)

    if not rq.GET.get('projectstatus') and not rq.GET.get('status'):
        pl = pl.filter(status='A')

    pl = pl.distinct()

    return pl