import csv
import json
import os
import subprocess
import warnings
from itertools import product

from crispy_forms.utils import render_crispy_form
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import FieldError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.forms import modelformset_factory
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.template import RequestContext, Context
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView
from django_tables2 import SingleTableView
from rest_framework.renderers import JSONRenderer
from rest_framework.utils.encoders import JSONEncoder
from six import BytesIO

from geo.models import District, Subdistrict, Suco, AdminArea
from nhdb import forms as nhdb_forms
from nhdb import forms_delete as nhdb_forms_delete
from nhdb import serializers
from nhdb.forms import *
from nhdb.forms_delete import *
from nhdb.tables import OrganizationTable, ProjectTable, PropertyTagTable, ProjectPersonTable, PersonProjectTable, \
    PersonTable
from rest_framework.parsers import JSONParser
from suggest.models import Suggest
from .views_helpers import projectset_filter, orgset_filter
from . import models
import logging

logger = logging.getLogger(__name__)


def object_index(queryset):
    """
    Return an index of primary keys with the last / next values in the queryset
    """
    pks = list(queryset.values_list('pk', flat=True))
    _index = {}
    for i, pk in enumerate(pks):
        _index[pk] = {}
        try:
            _index[pk]['next'] = pks[i + 1]
        except IndexError:
            _index[pk]['next'] = pks[0]
        try:
            _index[pk]['last'] = pks[i - 1]
        except IndexError:
            _index[pk]['last'] = pks[-1]
    return _index


def project_dashboard_info(projects, prefetch=True):
    dashboard = {}

    from collections import Counter

    projects = projects.prefetch_related('activity', 'beneficiary', 'sector')

    dashboard['activity'] = dict(Counter(projects.values_list('activity__name', flat=True)))
    dashboard['beneficiary'] = dict(Counter(projects.values_list('beneficiary__name', flat=True)))
    dashboard['sector'] = dict(Counter(projects.values_list('sector__name', flat=True)))

    project_places = projects.values_list('id', 'projectplace__place__path')
    project_districts = [(project_id, place_code[:3]) for project_id, place_code in project_places if place_code is not None]
    dashboard['district'] = dict(Counter([place_code for project_id, place_code in set(project_districts)]))

    return dashboard


def index(request):
    return render(request, 'nhdb/index.html')


class PersonDetail(DetailView):
    model = Person

    def get_context_data(self, **kwargs):
        context = super(PersonDetail, self).get_context_data(**kwargs)
        context['object'] = self.object
        # context['deleteform'] = PersonDeleteForm(instance=self.object)
        return context


class ProjectPersonDetail(DetailView):
    model = ProjectPerson


class ProjectPersonDelete(DetailView):
    model = ProjectPerson

    def get_context_data(self, **kwargs):
        context = super(ProjectPersonDelete, self).get_context_data(**kwargs)
        context['object'] = self.object
        context['deleteform'] = ProjectPersonDeleteForm(projectperson=self.object)
        return context


class PersonCreate(CreateView):
    model = Person

    def get_context_data(self, **kwargs):
        return {'form': PersonForm(instance=Person())}


class PersonList(SingleTableView):
    model = Person
    table_class = PersonTable

    # template_name = 'nhdb/projectperson_project_list.html'
    # paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super(PersonList, self).get_context_data(**kwargs)
        g = self.request.GET.getlist
        context['tabs'] = {'first': {'disabled': True}, 'fourth': {'disabled': True}}
        context['org'] = Organization.objects.filter(pk__in=g('org'))
        context['project'] = Project.objects.filter(pk__in=g('project'))

        return context

    def get_queryset(self):
        g = self.request.GET.getlist

        persons = Person.objects.all()

        if g('org'):
            persons = persons.filter(organization_id__in=g('org'))
        if g('project'):
            persons = persons.filter(projectperson__project_id__in=g('project'))
        return persons.distinct()


class ProjectImageDetail(DetailView):
    model = ProjectImage

    def get_context_data(self, **kwargs):
        context = super(ProjectImageDetail, self).get_context_data(**kwargs)
        if self.request.GET.get('project'):
            _data = {'project': self.request.GET.get('project')}
        else:
            _data = None

        context['deleteform'] = ProjectImageDeleteForm(instance=self.object)
        context['object'] = self.object

        context['project'] = self.request.GET.get('project')
        if _data:
            context['form'] = ProjectImageForm(instance=self.object, _data=_data)
        else:
            context['form'] = ProjectImageForm(instance=self.object)

        return context


class ProjectImageDelete(DetailView):
    """
    Returns a simple AJAX confirmation form to be injected into a page through an asynchronous request
    """

    template_name = 'nhdb/projectimage_delete.html'
    model = ProjectImage

    def get_context_data(self, **kwargs):
        context = super(ProjectImageDelete, self).get_context_data(**kwargs)
        # context = {}
        # context['form'] = ProjectImageForm(instance = self.object)
        context['deleteform'] = ProjectImageDeleteForm(instance=self.object)
        context['object'] = self.object
        context['project'] = self.request.GET.get('project')
        context['form'] = ProjectImageForm(instance=self.object)

        return context


class ProjectOrganizationDelete(DetailView):
    """
    Returns a simple AJAX confirmation form to be injected into a page through an asynchronous request
    """

    template_name = 'nhdb/projectorganization_delete.html'
    model = ProjectOrganization

    def get_context_data(self, **kwargs):
        context = super(ProjectOrganizationDelete, self).get_context_data(**kwargs)
        # context = {}
        # context['form'] = ProjectImageForm(instance = self.object)
        context['deleteform'] = ProjectOrganizationDeleteForm(instance=self.object)
        context['object'] = self.object
        context['project'] = self.request.GET.get('project')

        return context


def projectimagecreate(request):
    context = {'project': request.GET.get('project')}
    # Search for an organization as a GET request
    # Otherwies use "Organization search" function

    if context['project']:
        data = {'project': Project.objects.get(pk=context['project']).pk}
    else:
        data = {}
    context['form'] = ProjectImageForm(_data=data, data=data)

    return render(request, 'nhdb/projectimage_create.html', context)


class OrganizationDetail(DetailView):
    model = Organization

    def get_context_data(self, **kwargs):
        context = super(OrganizationDetail, self).get_context_data(**kwargs)
        context['suggestions'] = Suggest.objects.suggest(self.object)
        context['initialFeatures'] = OrganizationPlace.organization_place_feature_collection(
            {'organization_id': self.object.pk}, as_list=False)
        context['projectsets'] = {}
        for status in ProjectStatus.objects.all():
            _projects = self.object.project_set.filter(status=status)
            if _projects:
                context['projectsets'][status.description] = _projects

        _filter = {'organization__id': self.object.pk, 'status__in': ['A', 'U']}
        if self.object.project_set.count != 0:
            context['project_act'] = Project.pivot_table(_filter=_filter, field_name='activity')
            context['project_inv'] = Project.pivot_table(_filter=_filter, field_name='sector')
            context['project_ben'] = Project.pivot_table(_filter=_filter, field_name='beneficiary')

            rel = Organization.objects.filter(
                projectorganization__project__organization__id=self.object.pk,
                projectorganization__project__in=self.object.project_set.filter(status='A')
            ).distinct().values_list('pk', 'name')

        return context


def projectproperties(request):
    context = {}
    project = Project.objects.get(id=int(request.GET.get('project')))
    context['project'] = project
    context['form'] = ProjectpropertiesForm(instance=project)
    # return context
    return render(request, 'nhdb/project_properties.html', context)


class PersonProjectList(SingleTableView):
    """
    Show an editable list of projects for a person
    """
    model = ProjectPerson  # shorthand for setting queryset = models.Car.objects.all()
    table_class = PersonProjectTable
    template_name = 'nhdb/projectperson_person_list.html'
    paginate_by = 10

    def get_queryset(self):
        person = self.request.GET.get('person')
        if not person:
            return ProjectPerson.objects.none()
        return ProjectPerson.objects.filter(person_id=int(person))

    def get_context_data(self, **kwargs):
        context = super(PersonProjectList, self).get_context_data(**kwargs)
        context['person'] = Person.objects.get(id=int(self.request.GET.get('person')))
        return context


def newprojectperson(request):
    """
    Links a project to a person
    OR
    Shows a "Create Person" form with an additional field for "project involvement"
    :param request:
    :return:
    """
    data = {}
    for param in 'person', 'project':
        if request.GET.get(param):
            data[param] = request.GET.get(param)

    context = {
        # Use 'project' to automatically add a person to a project on save
        'project': data.get('project'),
        'person': data.get('person'),
        'personform': PersonForm(data=data),
        # 'projectpersonform': PartialProjectPersonForm(data=data),
        # Use 'createperson' in conjunction with 'project' to show a 'create user' form rather than a user dropdown list
        'createperson': request.GET.get('createperson')
    }
    return render(request, 'nhdb/projectperson_form.html', context)


def newprojectorganization(request):
    """
    Links a project to a organization
    OR
    Shows a "Create Organization" form with an additional field for "project involvement"
    :param request:
    :return:
    """
    data = {}
    for param in 'organization', 'project':
        if request.GET.get(param):
            data[param] = request.GET.get(param)

    # If a "project" is specified, the "organization" form receives hidden inputs to trigger
    # the loading of a "Organization's ready; specify its involvement" form

    if data['project']:
        # A call to the SUGGEST API will return '/ndhb/projectorganization/new/?organization=_x_&project=y
        # where x = suggestion id and y = project id

        data['return_url'] = '/nhdb/projectorganization/new/'
        data['return_param'] = 'organization'
        data['return_param_passthrough'] = 'project %s' % (data['project'])
        data['_affected_instance'] = 'nhdb_project %s' % (data['project'])

    context = {
        # Use 'project' to automatically add a organization to a project on save
        'project': data.get('project'),
        'organization': data.get('organization'),
        'organizationform': OrganizationForm(_data=data),
        # 'projectorganizationform': PartialProjectOrganizationForm(data=data),
        'createorganization': request.GET.get('createorganization')
    }
    return render(request, 'nhdb/projectorganization_form.html', context)


class ProjectPersonList(ListView):
    """
    Show a list of people for a project instance
    """
    model = ProjectPerson
    table_class = ProjectPersonTable
    template_name = 'nhdb/projectperson_project_list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(ProjectPersonList, self).get_context_data(**kwargs)
        # context['project'] = Project.objects.get(id=int(self.request.GET.get('project')))
        # context['personform'] = PersonForm()
        # context['projectpersonform'] = PartialProjectPersonForm()

        return context

    def get_queryset(self):
        project = self.request.GET.get('project')
        if not project:
            return ProjectPerson.objects.none()
        return ProjectPerson.objects.filter(project_id=int(project))


class ProjectOrganizationList(ListView):
    """
    Show a list of people for a project instance
    """
    model = ProjectOrganization
    template_name = 'nhdb/projectorganization_list.html'

    def get_context_data(self, **kwargs):
        context = super(ProjectOrganizationList, self).get_context_data(**kwargs)
        context['project'] = Project.objects.get(id=int(self.request.GET.get('project')))
        context['organizationform'] = OrganizationForm()
        # context['projectorganizationform'] = PartialProjectOrganizationForm()
        return context

    def get_queryset(self):
        project = self.request.GET.get('project')

        if not project:
            return ProjectOrganization.objects.none()
        return ProjectOrganization.objects.filter(project_id=int(project))


class ExcelDownloadFeedbackList(ListView):
    """
    Show a list of people for a project instance
    """
    model = ExcelDownloadFeedback
    # template_name = 'nhdb/excel.html'


def get_organization_queryset(request, filter_parameter='q'):
    """
        Returns a set of django 'Q' ('or') filters
        """
    logger.debug('Filtering organizations')

    inv = Q()
    act = Q()
    ben = Q()
    type = Q()
    district = Q()
    org_location = Q()
    status = Q()
    name = Q()
    filters = request.GET.getlist(filter_parameter)
    for _f in filters:
        if _f.lower().startswith('inv.'):
            inv = inv | Q(project__sector__path=_f.upper(), project__status='A')
        elif _f.lower().startswith('act.'):
            act = act | Q(project__activity__path=_f.upper(), project__status='A')
        elif _f.lower().startswith('ben.'):
            ben = ben | Q(project__beneficiary__path=_f.upper(), project__status='A')
        elif _f.lower().startswith('orgtype'):
            type = type | Q(orgtype=_f.split('.')[1].upper())
        elif _f.lower().startswith('district'):
            district = district | Q(project__place__path__startswith=_f.split('.')[1].upper())
        elif _f.lower().startswith('org_location'):
            path = _f.split('.')[1].upper()
            org_location = org_location | Q(organizationplace__point__intersects=District.objects.get(path=path).geom)

        elif _f.lower() == ('active.true'):
            status = status | Q(active=True)
        elif _f.lower() == ('active.false'):
            status = status | Q(active=False)

        elif _f.lower().startswith('name'):
            name = Q(name__icontains=_f.split('.')[1])

        if 'active.false' not in filters and 'active.any' not in filters:
            status = status | Q(active=True)

    if request.GET.get('name'):
        name = Q(name__icontains=request.GET.get('name'))
    logger.debug(filters)
    return Organization.objects.filter(inv).filter(ben).filter(act).filter(type).filter(district).filter(status).filter(
        org_location).filter(name).distinct()


def get_projects_page(request, filter_parameter='q'):
    def translatedfilter(parameters, filter_values, filter_type="icontains"):

        # For compatibility with "django-modeltranslation" expand a nonspecific filter such as "name" to "name_en",
        # "name_pt" etc
        _q = Q()
        for language, parameter, value in product(settings.LANGUAGES_FIX_ID, parameters, filter_values):
            filter_name = '%s_%s__%s' % (parameter, language[0], filter_type)
            __filter = {filter_name: value}
            _q = _q | Q(**__filter)

        return _q

    inv = Q()
    act = Q()
    ben = Q()
    type_ = Q()
    district = Q()
    status = Q()

    for _f in request.GET.getlist(filter_parameter):

        if _f.lower().startswith('inv.'):
            inv = inv | Q(sector__path=_f.upper())
        elif _f.lower().startswith('act.'):
            act = act | Q(activity__path=_f.upper())
        elif _f.lower().startswith('ben.'):
            ben = ben | Q(beneficiary__path=_f.upper())
        elif _f.lower().startswith('district'):
            district = district | Q(place__path__startswith=_f.split('.')[1].upper())
        elif _f.lower().startswith('status'):
            status = status | Q(status=_f.split('.')[1].upper())

    # By default restrict to 'active.true' only
    if status.children == []:
        status = status | Q(status='A')

    exclude = Q()

    for exclude_filter in request.GET.getlist('-' + filter_parameter):

        if exclude_filter.lower().startswith('inv.'):
            exclude = exclude | Q(sector__path=exclude_filter.upper())
        elif exclude_filter.lower().startswith('act.'):
            exclude = exclude | Q(activity__path=exclude_filter.upper())
        elif exclude_filter.lower().startswith('ben.'):
            exclude = exclude | Q(beneficiary__path=exclude_filter.upper())
        elif exclude_filter.lower().startswith('district'):
            exclude = exclude | Q(place__path__startswith=exclude_filter.split('.')[1].upper())
        elif exclude_filter.lower().startswith('status'):
            exclude = exclude | Q(status=exclude_filter.split('.')[1].upper())

    projects = Project.objects.filter(inv).filter(ben). \
        filter(act).filter(type_).filter(district).filter(status).distinct()

    projects = projects.exclude(exclude)

    sort = request.GET.get('sort')
    if sort:
        projects = projects.order_by(sort)

    text = request.GET.getlist('text')
    if text:
        # Split on ','
        for i in text:
            if ',' in i:
                text.extend(i.split(','))
        text = [i.strip() for i in text]
        projects = projects.filter(translatedfilter(parameters=['name', 'description'], filter_values=text))
    orgs = [i for i in request.GET.getlist('org') if i.isdigit()]
    if orgs:
        projects = projects.filter(organization__pk__in=orgs)

    return projects


def get_projects_paginated(request):
    projects = get_projects_page(request)
    paginator = Paginator(projects, request.GET.get('per_page', 50))
    page = request.GET.get('page', 1)

    try:
        projects_page = paginator.page(page)
    except PageNotAnInteger:
        projects_page = paginator.page(1)
    except EmptyPage:
        projects_page = paginator.page(paginator.num_pages)

    return projects_page


def downloadexcel(request):
    """
    Asks the user some questions for feedback purposes, returns a form object with a link to the
    download Excel page
    :return:
    """
    if request.POST:
        f = ExcelDownloadForm(request.POST or None)
        if f.is_valid():
            f.save()
            return HttpResponse(status=200)  # Success
        else:
            request_context = RequestContext(request)
            form_html = render_crispy_form(f, context=request_context)
            return HttpResponse(form_html, status=400)

    context = {'url': request.GET.get('next'), 'form': ExcelDownloadForm}
    return render(request, 'nhdb/crispy_form.html', context)


def organizationlist(request, pk=None):
    def org_dashboard_info(organizations):
        dashboard = {}
        dashboard['orgtype'] = {}
        for c in OrganizationClass.objects.filter(organization__in=organizations).annotate(Count('organization')):
            dashboard['orgtype'][c] = c.organization__count
        return dashboard

    r = request
    g = r.GET
    get = r.GET.get
    gl = r.GET.getlist

    context = {'propertytag_root_nodes': PropertyTag.get_root_nodes()}

    context['filters'] = {
        'inv': PropertyTag.objects.filter(path__startswith="INV."),
        'act': PropertyTag.objects.filter(path__startswith="ACT."),
        'ben': PropertyTag.objects.filter(path__startswith="BEN."),
        'district': [{'value': 'district.{}'.format(d[1].upper()), 'label': d[0]} for d in
                     District.objects.values_list('name', 'path')],
        'org_location': [{'value': 'org_location.{}'.format(d[1].upper()), 'label': d[0]} for d in
                         District.objects.values_list('name', 'path')],
        'type': [{'value': 'orgtype.{}'.format(o.pk), 'label': o} for o in OrganizationClass.objects.all()]
    }

    if list(g.values()) == []:
        context['form'] = OrganizationSearchForm()
    else:
        context['form'] = OrganizationSearchForm(request.GET)

    organizations = get_organization_queryset(r). \
        prefetch_related('organizationplace_set'). \
        prefetch_related('orgtype')

    filter_parameter = 'q'
    context['activefilters'] = gl(filter_parameter)
    context['dashboard'] = org_dashboard_info(organizations)
    context['object_class_count'] = Organization.objects.count()
    context['table'] = OrganizationTable(organizations)
    context['table'].paginate(page=get('page', 1), per_page=get('per_page', 50))
    context['excelform'] = ExcelDownloadForm({'referralurl': request.build_absolute_uri()})
    return render(request, 'nhdb/organization_list.html', context)


def organization_list_as_json(request):
    """
    Returns Organizations grouped
    :param request:
    :return:
    """
    organizations, projects = orgset_filter(request)
    return HttpResponse(json.dumps([org.name for org in organizations]), content_type='application/json')


def organizationdescription(request, pk, language_code):
    """
    Loads a rich text editor to push a description in the selected language as a suggestion to "Suggest.suggest"
    """
    instance = Organization.objects.get(pk=pk)
    my_field = 'description_' + language_code

    data = {}
    data['id'] = instance.id
    data['description'] = getattr(instance,
                                  my_field) or '<h2>About {}</h2><p>Enter details about this organization here</p>'.format(
        instance.name)
    data['language'] = language_code
    context = {'form': OrganizationDescriptionForm(data), 'basesuggestionform': BaseSuggestionForm(), 'pk': pk}
    return render(request, 'nhdb/organizationdescription.html', context)


def organizationsuggestions(request):
    context = {'suggestions': Suggest.objects.filter(affectedinstance__model_name='nhdb_organization',
                                                     affectedinstance__primary=True)}
    return render(request, 'nhdb/organizationsuggestions.html', context)


def organizationsuggestion(request, suggestion_pk):
    context = {'suggestion': Suggest.objects.get(pk=suggestion_pk)}

    return render(request, 'nhdb/organizationsuggestion.html', context)


def projectdescription(request, pk, language_code):
    """
    Loads a rich text editor to push a description in the selected language as a suggestion to "Suggest.suggest"
    :param UpdateView:
    :return:
    """
    instance = Project.objects.get(pk=pk)
    my_field = 'description_' + language_code

    data = {}
    data['id'] = instance.id
    data['description'] = getattr(instance,
                                  my_field) or '<h2>About {}</h2><p>Enter details about this organization here</p>'.format(
        instance.name)
    data['language'] = language_code
    context = {'form': ProjectdescriptionForm(data), 'pk': pk}
    return render(request, 'nhdb/projectdescription.html', context)


def confirmprojectchange(request, suggest_pk):
    """
    Loads information from a requested change
    :param UpdateView:
    :return:
    """
    # Populate a Project Form with information from the Suggest table

    if request.method == "GET":
        update = Suggest.objects.get(pk=suggest_pk)
        current = serializers.ProjectSerializer(Project.objects.get(pk=update.model_pk))

        # Compare the differences between the current model and new model
        suggested = serializers.ProjectSerializer(data=JSONParser().parse(BytesIO(update.serialized)))
        context = {}


def organizationupdate(request, form="main"):
    organization = request.GET.get('organization')
    if organization:
        organization = Organization.objects.get(pk=organization)

    suggestion = request.GET.get('suggestion')
    if suggestion:
        suggestion = Suggest.objects.get(pk=suggestion)

    context = {}

    if form == 'main':
        context['form'] = OrganizationForm(instance=organization, suggestion=suggestion)
    elif form == 'contact':
        context['form'] = OrganizationcontactForm(instance=organization, suggestion=suggestion)
    # elif form == 'place':
    # context['form'] = OrganizationPlaceForm(_data={'organization': organization}, instance = OrganizationPlace.objects.get(pk = form_object_pk))

    elif form == 'description':
        language = request.GET.get('language', 'en')
        context['form'] = OrganizationDescriptionForm(language=language, organization=organization,
                                                      suggestion=suggestion)

    elif form == 'delete':
        context['form'] = OrganizationDeleteForm(instance=organization)

    return render(request, 'nhdb/crispy_form.html', context)


class OrganizationCreate(CreateView):
    model = Organization
    form_class = OrganizationForm


class OrganizationDelete(DeleteView):
    model = Organization


class ProjectDetail(DetailView):
    model = Project

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)
        context['suggestionswaiting'] = Suggest.objects.suggest(self.object).filter(state__in=['W'])
        context['suggestions'] = Suggest.objects.suggest(self.object).filter(state__in=['A'])
        # context['placeform'] = ProjectPlaceForm(instance=self.object)
        return context


class ProjectOrganizations(ListView):
    model = ProjectOrganization
    template_name = 'nhdb/projectorganization_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ProjectOrganizations, self).get_context_data(**kwargs)

        context['project'] = Project.objects.get(pk=self.kwargs.get('pk'))
        formset = modelformset_factory(ProjectOrganization, form=ProjectorganizationForm, extra=3)
        context['formset'] = formset(queryset=ProjectOrganization.objects.filter(project__pk=self.kwargs.get('pk')))
        context['organizationclass_objects'] = ProjectOrganizationClass.objects.all()

        return context

    def get_queryset(self, *args, **kwargs):
        organizations = ProjectOrganization.objects.filter(project__pk=self.kwargs.get('pk'))
        return organizations


@staff_member_required
def organization_persons(request, organization_id):
    """
    Contact list for people in the organization
    :param request:
    :param organization_id:
    :return:
    """
    organization = Organization.objects.get(pk=organization_id)
    persons = organization.person_set.all()
    context = {'organization': organization, 'persons': persons,
               # 'form': OrganizationAddPersonForm(organization=organization )
               }

    return render(request, 'nhdb/organization_persons.html', context)


def thumbnail_image(request):
    """
    Expects a GET parameter like request=/media/projectimage/100/20150818/star-512_0DXbMiK.jpg
    :param request:
    :return:
    """
    r = request.GET['request']
    s = r.split('/')
    res = s.pop(3)
    filename = '/webapps/project' + '/'.join(s)
    output_path = '/webapps/project' + r
    if not os.path.exists(os.path.split(output_path)[0]):
        os.makedirs(os.path.split(output_path)[0])

    # Call convert on the image path
    call = ['convert', filename, '-background', 'white', '-alpha', 'remove', '-resize', '%sx%s' % (res, res),
            'jpg:' + output_path]
    _c = ' '.join(call)
    subprocess.call(call)
    if not os.path.exists(output_path):
        raise AssertionError(_c)
    return HttpResponse(open(output_path).read(), content_type='image/jpg')


def projectcsv(request):
    headers = ['ID', 'Name', 'Project Description', 'Start Date', 'End Date', 'Notess', 'Status', 'Projecttype']

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="projects.csv"'

    writer = csv.writer(response)
    writer.writerow(headers)

    projects = projectset_filter(request)
    for p in projects:

        # It is necessary to decode to UTF-8 before writing to deal with accents
        # However decode fails on None for description and/or notes

        row = [p.id, p.name, p.description, p.startdate, p.enddate, p.notes, p.status, p.projecttype]
        parse = enumerate(row)
        for index, content in parse:
            if isinstance(content, str):
                row[index] = content.encode('utf-8')

        writer.writerow(row)

    return response


def projectcsv_nutrition(request):
    headers = ['No.', 'Project', 'Description', 'Start date', 'End date', 'Organizations', 'Places', 'Place Codes',
               'Activities', 'Beneficiaries', 'Sectors', 'Contacts']
    projects = projectset_filter(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="projects.csv"'

    writer = csv.writer(response)
    writer.writerow(headers)

    projects = projectset_filter(request)
    for p in projects:

        # It is necessary to decode to UTF-8 before writing to deal with accents
        # However decode fails on None for description and/or notes

        row = [p.id, p.name, p.description, p.startdate, p.enddate]

        organization_list = []

        vals = p.projectorganization_set.all().values('organization__name', 'organization__contact__phoneprimary',
                                                      'organization__contact__email')
        for org in vals:
            organization_list.append('%s (tel:%s, email:%s)' % (
                org['organization__name'], org['organization__contact__phoneprimary'],
                org['organization__contact__email']))
        organization_list = ', '.join(organization_list)
        place_list = ', '.join(p.place.values_list('name', flat=True))
        pcode_list = ','.join([str(i) for i in p.place.values_list('pcode', flat=True)])
        activity_list = ', '.join(p.activity.values_list('name', flat=True))
        ben_list = ', '.join(p.beneficiary.values_list('name', flat=True))
        sec_list = ', '.join(p.sector.values_list('name', flat=True))
        person_list = []
        for person in p.person.all():
            person_list.append('{} - {} - {}'.format(person.name, person.contact.email or "No email",
                                                     person.contact.phone or "No phone"))

        person_list = ', '.join(person_list)

        row.append(organization_list)
        row.append(place_list)
        row.append(pcode_list)
        row.append(activity_list)
        row.append(ben_list)
        row.append(sec_list)
        row.append(person_list)

        parse = enumerate(row)
        for index, content in parse:
            if isinstance(content, str):
                row[index] = content.encode('utf-8')

        writer.writerow(row)

    return response


def projectdashboard(request):
    c = {}
    tags = {}
    projects = get_projects_page(request, paginate=False)
    projectpks = projects.values_list('pk', flat=True)
    propertytags = PropertyTag.objects.select_related('project')

    # Construct a dictionary of tag path, tag name, and project count
    for tag_path, link in (('BEN', 'beneficiary'), ('ACT', 'activity'), ('INV', 'sector')):
        link_name = 'project_' + link
        tag = propertytags.get(path=tag_path)
        filters = {link_name + '__pk__in'.format(link_name): projectpks, 'path__startswith': tag_path + '.'}
        tags[tag.name_en] = list(
            propertytags.filter(**filters).annotate(count=Count(link_name)).values('name', 'path',
                                                                                   'count').order_by(
                'name'))

        # tags[tag.name_en].append({'name': 'none', 'count': Project.objects.annotate(c = Count(link)).filter(c=0).count(), 'path':None})

    status = {}
    for i in ProjectStatus.objects.filter(project__pk__in=projectpks).annotate(c=Count('project')):
        status[i.description] = i.c

    c['json'] = json.dumps({
        'tags': tags,
        'status': status
    })

    c['projects'] = projects
    c['places'], c['max_projects'] = projectplaces(request)

    return render(request, 'nhdb/project_dashboard.html', c)
    # return HttpResponse(json.dumps(c), content_type="application/json")


def projectplaces(request):
    """
    Return a JSON-encoded list of places and the number of projects filtered by GET parameters
    :return:
    """
    path = request.GET.get('path')
    projects = get_projects_page(request, paginate=False)
    if path is None:
        places = District.objects.all()
    elif path in District.objects.all().values_list('path', flat=True):
        places = Subdistrict.objects.filter(path__startswith=path)
    elif path in Subdistrict.objects.all().values_list('path', flat=True):
        places = Suco.objects.filter(path__startswith=path)
    else:
        places = AdminArea.objects.none()

    places = places.filter(project__in=projects).annotate(count=Count('project'))
    _max = max(places.values_list('count', flat=True))
    return places, _max


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



from django.contrib.postgres.fields import ArrayField
from django.db.models import Aggregate, IntegerField


class IntegerArray(Aggregate):
    function = 'ARRAY_AGG'
    template = '%(function)s(%(distinct)s%(expressions)s)'

    def __init__(self, expression, distinct=True, **extra):
        super(IntegerArray, self).__init__(
            expression,
            distinct='DISTINCT ' if distinct else '',
            output_field=ArrayField(IntegerField()),
            **extra
        )


def object_dump(object, indent=None):
    return mark_safe(json.dumps(object, indent=indent, cls=JSONEncoder))


class OfflineContent():

    def __init__(self, timestamp=0.0, now=datetime.now().timestamp()):
        projects = Project.objects.all() \
            .annotate(orgs=IntegerArray('projectorganization__organization')) \
            .annotate(places=IntegerArray('projectplace__place')) \
            .annotate(sector_=IntegerArray('sector')) \
            .annotate(activity_=IntegerArray('activity')) \
            .annotate(beneficiary_=IntegerArray('beneficiary'))

        organizations = models.Organization.objects.all()
        propertytag = models.PropertyTag.objects.all()
        self.since = datetime.fromtimestamp(float(timestamp))
        self.datasets = (
            ('Project', projects,
             ['pk', 'name', 'description', 'startdate', 'enddate', 'orgs', 'status', 'places', 'sector_',
              'activity_', 'beneficiary_']),
            ('Organization', organizations, ['pk']),
            ('PropertyTag', propertytag, ['pk', 'name']),
            ('ProjectStatus', models.ProjectStatus.objects.all(), ['pk', 'project__pk', 'code']),
            ('ProjectOrganization', models.ProjectOrganization.objects.all(),
             ['pk', 'project__pk', 'organization', 'organizationclass']),
            ('OrganizationClass', models.OrganizationClass.objects.all(), ['pk', 'code', 'orgtype']),
            ('ProjectPerson', models.ProjectPerson.objects.all(), ['pk', 'project', 'person', 'is_primary']),
            ('Person', models.Person.objects.all(), ['pk', 'name', 'title', 'organization']),
            ('settings', [{'key': 'lastupdated', 'value': now}], ['key', 'value']),
        )

    @property
    def dexie_tables(self):
        return {dataset[0]: ', '.join(dataset[2]) for dataset in self.datasets}

    @property
    def timestamped_models(self):

        def list_values(objects, values, since=datetime.fromtimestamp(0)):

            if not hasattr(objects, 'filter'):
                return {
                    'created': objects,
                    'updated': [],
                    'deleted': [],
                }

            try:
                created = objects.filter(created_at__gte=since, deleted_at__isnull=True)
                updated = objects.filter(updated_at__gte=since, created_at__lt=since, deleted_at__isnull=True)
                deleted = objects.filter(created_at__lte=since, deleted_at__gte=since)

            except FieldError:
                warnings.warn('Expected created_at, updated_at, deleted_at fields in query')
                created = objects.all()
                updated = objects.none()
                deleted = objects.none()

            return {
                'created': created.values(*values),
                'updated': updated.values(*values),
                'deleted': deleted.values('pk')
            }

        return {
            name: {
                'columns': columns,
                'data': list_values(objects, columns, self.since)
            }
            for name, objects, columns in self.datasets
        }


class MainJS(TemplateView):
    template_name = 'riot/database.j2'
    content_type = 'application/javascript'

    def get_content_type(self):
        return 'application/javascript'

    def get_context_data(self, **kwargs):
        context = {}
        now = datetime.now().timestamp()
        timestamp = float(self.request.GET.get('timestamp', 0))
        db = OfflineContent(timestamp, now)
        if 'timestamp' in self.request.GET:
            context['objects'] = object_dump(db.timestamped_models)

        context['dexied'] = object_dump(db.dexie_tables, indent=1)
        # TODO: Store this value so that it can be compared and autoincremented
        context['db_name'] = 'database'
        context['db_version'] = '0.1'
        context['now'] = now
        return context


class Main(TemplateView):
    template_name = 'riot/project_list.html'
    # content_type = 'application/html'


def projectlist(request):
    c = {}
    req = request
    getlist = req.GET.getlist
    get = req.GET.get

    c['ip'] = get_client_ip(req)
    if getlist('org'):
        c['organization'] = Organization.objects.filter(pk__in=[i for i in getlist('org') if i.isdigit()])

    c['filters'] = {
        'inv': PropertyTag.objects.filter(path__startswith="INV."),
        'act': PropertyTag.objects.filter(path__startswith="ACT."),
        'ben': PropertyTag.objects.filter(path__startswith="BEN."),
        'district': [{'value': 'district.{}'.format(d[1].lower()), 'label': d[0]} for d in
                     District.objects.values_list('name', 'path')],
        'type': [{'value': 'orgtype.{}'.format(o.pk), 'label': o} for o in OrganizationClass.objects.all()],
        'status': [{'value': 'status.{}'.format(o.pk), 'label': o} for o in ProjectStatus.objects.all()]
    }

    filter_parameter = 'q'
    c['activefilters'] = getlist(filter_parameter)
    c['activeexcludes'] = getlist('-' + filter_parameter)

    c['searchdescription'] = {}
    # Build a human readable translation of the search filters
    c['excelform'] = ExcelDownloadForm({'referralurl': request.build_absolute_uri()})

    if c['activefilters'] or c['activeexcludes']:
        c['searchdescription'] = {  # List of search parameters in human readable form
            "Sector ": PropertyTag.objects.filter(
                path__in=[i for i in c['activefilters'] if i.startswith('INV.')]).values_list('name',
                                                                                              flat=True),
            "NOT Sector ": PropertyTag.objects.filter(
                path__in=[i for i in c['activeexcludes'] if i.startswith('INV.')]).values_list('name',
                                                                                               flat=True),
            "Beneficiary ": PropertyTag.objects.filter(
                path__in=[i for i in c['activefilters'] if i.startswith('BEN.')]).values_list('name',
                                                                                              flat=True),
            "NOT Beneficiary ": PropertyTag.objects.filter(
                path__in=[i for i in c['activeexcludes'] if i.startswith('BEN.')]).values_list('name',
                                                                                               flat=True),
            "Activity ": PropertyTag.objects.filter(
                path__in=[i for i in c['activefilters'] if i.startswith('ACT.')]).values_list('name',
                                                                                              flat=True),
            "NOT Activity ": PropertyTag.objects.filter(
                path__in=[i for i in c['activeexcludes'] if i.startswith('ACT.')]).values_list('name',
                                                                                               flat=True),
            "In districts": District.objects.filter(
                path__in=[i.replace('district.', '').upper() for i in c['activefilters'] if
                          i.startswith('district.')]).values_list('name', flat=True),
        }

    status = [i for i in c['activefilters'] if i.startswith('status')]
    if not status:
        c['activefilters'].append('status.A')

    else:
        c['search'] = "All active projects"

    c['searchdescription']['status'] = [i for i in c['activefilters'] if
                                        i.startswith('status')] or 'Active'
    c['activesort'] = get('sort')
    c['text'] = get('text')
    # Edge case where sometimes "None" is taken as literal text
    if not c['text'] or c['text'] == 'None':
        c['text'] = ''

    c['object_class_count'] = Project.objects.count()

    c['tabs'] = {'first': {'name': 'Search'}}
    object_list = get_projects_page(req)
    c['object_list_count'] = object_list.count()
    c['dashboard'] = project_dashboard_info(object_list)
    c['table'] = ProjectTable(
        # paginated.object_list.prefetch_related('organization', 'sector', 'status')
        object_list.prefetch_related('organization', 'sector', 'status')
    )
    c['table'].paginate(page=get('page', 1), per_page=get('per_page', 50))

    return render(request, 'nhdb/project_list.html', c)


def search(request, model, languages='en'):
    """
    Returns matching objects for a selectize.js list
    :param request:
    :param model:
    :return:
    """
    if not hasattr(model, 'objects'):
        model = globals()[model.capitalize()]
        assert hasattr(model, 'objects'), 'Please pass a model instance or name to this function'

    model_field_names = model._meta.get_all_field_names()

    fields = request.GET.getlist('fields', ['name'])
    search_term = request.GET.get('search', 'Jackson')

    q = Q()
    kweries = {}
    for field_name in fields:
        if field_name not in model_field_names:
            raise NameError('There is no field called %s in the model %s' % (field_name, model._meta.verbose_name))
        kweries[field_name + '__icontains'] = search_term
        kwery = {field_name + '__icontains': search_term}
        q = q | Q(**kwery)

        # If this is a translated field: search all translated languages
        for language in settings.LANGUAGES_FIX_ID:
            translated_field_name = field_name + '_' + language[0]
            if translated_field_name in model_field_names:
                kweries[translated_field_name + '__icontains'] = search_term
                kwery = {translated_field_name + '__icontains': search_term}
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


class PropertyTagList(SingleTableView):
    model = PropertyTag
    table_class = PropertyTagTable

    def get_context_data(self, **kwargs):
        context = super(PropertyTagList, self).get_context_data(**kwargs)
        context['form'] = PropertyTagForm()
        return context


def propertytagselect(request):
    media = {
        'js': ['tree-multiselect.js/dist/jquery.tree-multiselect.min.js'],
        'css': ['tree-multiselect.js/dist/jquery.tree-multiselect.min.css'],
    }

    s = mark_safe('<select id="test" multiple="multiple">')
    for i in PropertyTag.objects.all().order_by('path'):
        if len(i.path) == PropertyTag.steps:
            data_section = i.name
            continue
        else:
            data_section = ''
        option = {'pk': i.pk, 'name': i.name, 'data-section': data_section, 'data-description': i.description}
        if i.pk in request.GET.getlist('s'):
            option['selected'] = 'selected="selected"'
        else:
            option['selected'] = ''
        s += mark_safe(
            '\n\t<option value="{pk}" data-section="{data-section}" {selected}>{name}</option>'.format(**option))

    s += mark_safe('\n</select>')
    return render(request, 'content_test.html', {'content': s, 'media': media})


def partners(request):
    organizations = Organization.objects.filter(orgtype="INGO", active=True)
    organizations.select_related()
    context = {'organizations': organizations}
    return render(request, 'nhdb/partners.html', context)


def form(request, model=None, form='main'):
    args = {}
    f = None
    g = request.GET.get
    template = 'nhdb/crispy_form.html'
    app_name = 'nhdb'

    from django.apps import apps

    g = request.GET.get
    args = {}
    args['nochange'] = []

    models = apps.get_app_config(app_name).models
    for m_name in models:
        m = models[m_name]

        if g(m_name):
            # try:
            args[m_name] = m.objects.get(pk=g(m_name))
            # except m.DoesNotExist:
            #    return HttpResponse("This object does not exist in the database: {} (id = {})".format(m_name,g(m_name), status=404)

        #  Use an exclamation to indicate a field which should not be changable
        if g('!' + m_name):
            args[m_name] = m.objects.get(pk=g('!' + m_name))
            args['nochange'].append(m_name)

        # Use an underscore to indicate a suggestion ID
        elif g('_' + m_name):
            args[m_name] = Suggest.objects.get(pk=g('_' + m_name))

    if model == 'project':
        if form == 'main':
            f = ProjectForm
        if form == 'delete':
            f = ProjectDeleteForm
        if form == 'properties':
            f = ProjectpropertiesForm
        if form == 'organization':
            f = ProjectorganizationForm
        if form == 'description':
            args['language'] = request.GET.get('language', 'en')
            f = ProjectdescriptionForm

        if form == 'translation':
            f = ProjectTranslationsForm

    if model == 'projectimage':
        if form == "delete":
            f = ProjectImageDeleteForm
        if form == 'main':
            f = ProjectImageForm

    if model == 'projectperson':

        # Allow a projectperson to be specified based on a "project" and a "person"
        if 'project' in args and 'person' in args:
            args['instance'] = ProjectPerson.objects.get(project=args['project'], person=args['person'])
        if form == "delete":
            assert args['projectperson']
            f = ProjectPersonDeleteForm
        elif form == 'main':
            f = ProjectPersonForm

    if model == 'person':

        if form == "main":
            f = PersonForm
            # elif form == "delete":
            #     f = PersonDeleteForm

    if model == 'projectplace':
        if request.GET.get('place'):
            args['place'] = AdminArea.objects.get(pk=request.GET.get('place'))
        if request.GET.get('project'):
            args['project'] = Project.objects.get(pk=request.GET.get('project'))

    if model == 'projectorganization':

        if form == 'main':
            f = ProjectorganizationForm
        if form == 'delete':
            f = ProjectOrganizationDeleteForm

    if model == 'organization':
        if form == 'description':
            args['language'] = g('lang') or 'en'
            f = OrganizationDescriptionForm
        if form == 'main':
            f = OrganizationForm
        if form == 'contact':
            f = OrganizationcontactForm
        if form == 'delete':
            f = OrganizationDeleteForm

    if f:
        return render(request, template, {'form': f(**args)})

    else:
        if form == 'main':
            f_name = '%sForm' % model.title()
        elif form == 'delete':
            f_name = '%s%sForm' % (model.title(), 'Delete')
            if hasattr(nhdb_forms_delete, f_name):
                f = getattr(nhdb_forms_delete, f_name)
                return render(request, template, {'form': f(**args)})

        else:
            f_name = '%s%sForm' % (model.title(), form.upper())

        if hasattr(nhdb_forms, f_name):
            f = getattr(nhdb_forms, f_name)
            return render(request, template, {'form': f(**args)})

        # Else if there's a case error, try to match the name anyway
        for i in dir(nhdb_forms):
            if i.lower() == f_name.lower():
                f = getattr(nhdb_forms, i)
                return render(request, template, {'form': f(**args)})

        return HttpResponseBadRequest(
            mark_safe("<form>Class nhdb.forms.{} is not defined yet</form>".format(f_name)))


def project_verification(request):
    context = {'projects': Project.objects.order_by('-verified')}
    return render(request, 'nhdb/project_verification.html', context)


def lookup_tables(request):
    '''
    Returns a JSON dict of lookup id/names for certain fields
    :param request:
    :return:
    '''

    lookups = {
        'organization': [(str(o), o.id) for o in Organization.objects.all()],
        'properties': [(str(o), o.id) for o in PropertyTag.objects.all()],
    }
    return HttpResponse(json.dumps(lookups, indent=1), content_type='application/json')
