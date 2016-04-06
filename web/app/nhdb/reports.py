from django.shortcuts import render, render_to_response
from django.http import HttpResponse
#~ from django.template import Context, loader, RequestContext
from nhdb.models import *
from census.models import Place
import census
import datetime
import json
import string
#from mptt.models import MPTTModel
from django.db.models import Count
from nhdb.views_helpers import *

def filterBySector(projects, sector, sector_pk):

    if sector == 'ben':
        sector = Beneficiary.objects.get(pk = sector_pk)
        projects = projects.filter(beneficiary = Beneficiary.objects.get(pk = sector_pk))
    elif sector == 'inv':
        sector = Involvement.objects.get(pk = sector_pk)
        projects = projects.filter(involvement = Involvement.objects.get(pk = sector_pk))
    elif sector == 'act':
        sector = Activity.objects.get(pk = sector_pk)
        projects = projects.filter(activity = Activity.objects.get(pk = sector_pk))

    return projects

def getlabel(m):
    '''
    Try different labels: first __unicode__() method, then 'name', property, then 'description' property
    '''
    try:
        return m.__unicode__()
    except:
        pass

    try:
        return m.name
    except:
        pass

    try:
        return m.description
    except:
        pass
        
    raise AttributeError, 'No suitable label found. Need one of: %s'%dir(m)

def place_count(projects = Project.objects.all(), place = None):
    '''
    Take a queryset, return count of projects in this district
    '''
    
    def perPlace(place, projects):
        pers   = place.persons or 1
        pcount = projects.filter(place__in = childplace.get_descendants(include_self=True)).distinct()
        if place.path == 'TLS':
            pcount = projects.distinct()
        return pers, pcount

    if place == None or place.path == 'TLS':
        place = Place.objects.get(path='TLS')
        childplaces = Place.get_root_nodes()
    else:
        childplaces = place.get_descendants(include_self=False)
    
    _ret = []
    
    for childplace in childplaces:
        pers, pcount = perPlace(childplace, projects)

        name = childplace.name

        if name.startswith('Distrito De'):
            name = name[12:]

        _ret.append({
            'name':name,
            'path':childplace.path, 
            'projects':pcount.count(),
            'projects_per_10000':round((pcount.count() * 10000)/(pers * 1.0), 2),
            'persons':pers
            })
   
    return _ret

def timeseries(projects):
    '''
    Create a timeseries graph of projects over time
    '''
    def jsts(dt):
        '''
        Python to Javascript timestamp (JS = milliseconds since Jan 1 1970)
        '''
        if dt == None:
            return None
        delta = dt - datetime.date(1970,1,1)
        return delta.days *24*60*60*1000

    dates = [(p.startdate, 1) for p in projects.filter(startdate__isnull=False, status=1)]
    enddates = [(p.enddate, -1) for p in projects.filter(startdate__isnull=False, enddate__isnull=False, status=1)]
    dates.extend(enddates)
    
    date_projectcount = []
    running_total = 0
    dates.sort()
    for d in dates:
        if d[0] is None or d[0] > datetime.date.today():
            continue
        running_total += d[1]
        if len(date_projectcount) > 0:
            if d[0] == date_projectcount[-1][0]:
                date_projectcount.pop()
        date_projectcount.append([jsts(d[0]), running_total])

    return date_projectcount

def sectortimeseries(request, modelname, model_pk):
    '''
    Return a JSON encoded list suitable for plotting with Flot
    (or another JS library) of graphs in a sector over time
    '''

    kw = {modelsets(modelname)[1]:int(model_pk)}
    projects = Project.objects.filter(**kw)
    ts = timeseries(projects)

    return HttpResponse(json.dumps(ts, indent=1), content_type='application/json')

def allsectors(request):
    '''
    Summary page to show projects by sector for all districts compared to national average
    '''
    
    def projects(sector, place):
        '''
        Projects which are in a specific place and sector
        '''
        assert isinstance(place, Place)
        assert isinstance(sector, Involvement)

        projects = Project.objects.filter(status = True)
        projects = projects.filter(place__in = place.get_descendants())
        projects = projects.filter(involvement = Involvement)
        
        return projects
    
    sectors = Involvement.objects.all()
    
    if 'place' in request.GET:
        p = Place.objects.get(path = request.GET['place'])
    else:
        p = Place.objects.get(pk = 1)
        
    
    series = []

    for d in p.get_children():
        this_series = {'name':d.name,'data':[]}
        for s in sectors:
            this_series['data'].append(round(projects(s, d).count() * 100000.0 / d.persons(),1))
        series.append(this_series)

    this_series = {'name':p.name,'data':[]}
    for s in sectors:
        this_series['data'].append(round(projects(s, p).count() * 100000.0 / p.persons(), 1))
    series.append(this_series)
        
    context = {
        'categories':json.dumps(categories),
        'series':json.dumps(series),
        'title':'Project Distribution over Timor Leste',
        'div':'#chart',
        'type':'bar'}
        
    return render(request,'nhdb/highcharts.column.basic.js',context)

def allsectorshtml(request):
    if 'place' in request.GET:
        context = {'place':Place.objects.get(path = request.GET['place'])}
    return render(request, 'nhdb/report_allsector.html',context)
        
def sector(request, sector, sector_pk):
    '''
    Report about a particular aid sector; initially this will use 
    MainActivity but in future could use CRS codes
    '''
    
    def average_project_count(sector, depth):
        '''
        Get the average project count for all places
        
        depth = 1 to 4 (country / district/ subdistrict / suco)
        sector = option for project
        '''
        projectplacecount = ProjectPlace.objects.filter(project__option = sector).count()
        placecount = Place.objects.filter(depth = depth)
        
        projects_per_place = float(projectplacecount) / placecount
        return projects_per_place
    
    def project_fair(sector, place):
        '''
        Get the 'fair' number of projects for a place in a given sector
        Compares the number of projects and population level to other
        places at the same administration level (ie suco w/ suco)
        '''
        depth = place.depth
        projects_per_place = average_project_count(sector, depth)
        
    #sector = get_sector(sector, sector_pk)
    
    projects = projectset_filter(request, Project.objects.all())
    projects = projects.filter(status=True)
    
    if 'place' in request.GET:
        place = Place.getfromstring(request.GET['place'])

    else:
        place = Place.getfromstring('TLS')

    projects = filterBySector(projects, sector, sector_pk)

    projpks = projects.values_list('pk',flat=True)
    
    tb = Beneficiary.objects.all()
    tb = tb.filter(project__pk__in=projpks, project__status=True)
    tb = tb.annotate(count = Count('project')).order_by('-count')
        
    ma = Activity.objects.all()
    ma = ma.filter(project__pk__in=projpks, project__status=True)
    ma = ma.annotate(count = Count('project')).order_by('-count')

    #return HttpResponse(json.dumps(place_count(sector, projects, place), indent=1), content_type='application/json')

    return render(request, 'nhdb/report_sector.html', {
        'sector':sector, 
        'targetbeneficiaries':tb, 
        'mainactivities':ma,
        'place_count':place_count(projects, place),
        'date_projectcount':timeseries(projects)
        })
