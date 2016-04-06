import StringIO
from datetime import datetime, time
from itertools import product
import subprocess
import json
import csv

from belun import settings
from django.forms import modelformset_factory
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic import DetailView, ListView
from geo.models import District, Subdistrict, Suco, AdminArea
from nhdb.models import Organization, PropertyTag, Project, ProjectPerson, Person, ProjectOrganization, \
    OrganizationPlace, ProjectStatus, ProjectOrganizationClass, OrganizationClass, ProjectImage, ProjectPlace
from django_tables2 import SingleTableView
from nhdb import forms as nhdb_forms
from nhdb.forms_delete import *
from nhdb import forms_delete as nhdb_forms_delete
from nhdb.forms import *
from nhdb.tables import OrganizationTable, ProjectTable, PropertyTagTable, ProjectPersonTable, PersonProjectTable, \
    PersonTable
import os
from six import BytesIO
from suggest.models import Suggest, AffectedInstance
from views_helpers import projectset_filter, orgset_filter
from django.db.models import Q, Count, QuerySet
from rest_framework.parsers import JSONParser
import warnings
from nhdb import serializers
from django.contrib.admin.views.decorators import staff_member_required
import xlsxwriter

languages = (('en', 'English'), ('tet', 'Tetun'), ('pt', 'Portugese'), ('id', 'Bahasa'))


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
    dashboard['district'] = {}

    k = {'ACT':'activity', 'BEN':'beneficiary', 'INV':'sector'}

    for i in PropertyTag.objects.filter(path__in = k.keys()):
        name = k.get(i.path)
        dashboard[i] = {}
        filter = {'project_%s__in'%name:projects}
        anno = Count('project_%s'%name)
        # dashboard[i][pt] = pt.project_activity__count

        for pt in PropertyTag.objects.all() \
                .filter(**filter) \
                .annotate(anno):
            dashboard[i][pt] = getattr(pt, 'project_%s__count'%name)

    pplist = ProjectPlace.objects.filter(project__in=projects).values_list('project__id', 'place__path')
    for d in District.objects.all():
        dashboard['district'][d] = len(set([(i[0], i[1][:3]) for i in pplist if i[1][:3] == d.path]))

    return dashboard


def org_dashboard_info(organizations):
    dashboard = {}
    dashboard['orgtype'] = {}
    for c in OrganizationClass.objects.filter(organization__in=organizations).annotate(Count('organization')):
        dashboard['orgtype'][c] = c.organization__count
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
        context['deleteform'] = ProjectPersonDeleteForm(instance=self.object)
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
    '''
    Returns a simple AJAX confirmation form to be injected into a page through an asynchronous request
    '''

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
    '''
    Returns a simple AJAX confirmation form to be injected into a page through an asynchronous request
    '''

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
    context = {}
    # Search for an organization as a GET request
    # Otherwies use "Organization search" function

    context['project'] = request.GET.get('project')

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


def get_organization_queryset(request, filter_parameter='q'):
    """
        Returns a set of django 'Q' ('or') filters
        """

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

    return Organization.objects.prefetch_related('organizationplace_set').filter(inv).filter(ben). \
        filter(act).filter(type).filter(district).filter(status).filter(org_location).filter(name).distinct()


def get_project_queryset(request, filter_parameter='q'):
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
    type = Q()
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
        filter(act).filter(type).filter(district).filter(status).distinct() \
        .prefetch_related('status') \
        .prefetch_related('organization')

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


def organization_table_excel(request):
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    worksheet.write('A9', 'Name')
    worksheet.set_column('A:A', 50)
    worksheet.set_column('B:B', 30)
    worksheet.set_column('C:C', 30)
    worksheet.set_column('D:D', 50)
    worksheet.write('B9', 'Phone')
    worksheet.write('C9', 'Email')
    worksheet.write('D9', 'Main address')
    code = request.LANGUAGE_CODE

    if code == 'tet':
        worksheet.write('A7', 'Database Nasional')  # TODO: Full title here
        worksheet.insert_image('A1', '/webapps/project/media/banner.jpg', options={'x_scale': 0.25, 'y_scale': 0.25})

    if code == 'en':
        worksheet.write('A7', 'National Database')  # TODO: Full title here
        worksheet.insert_image('A1', '/webapps/project/media/banner.jpg', options={'x_scale': 0.25, 'y_scale': 0.25})

    row = 9
    organizations = get_organization_queryset(request)
    for org in organizations:
        row += 1
        # Write some numbers, with row/column notation.

        phone = org.phoneprimary
        if org.phonesecondary:
            phone += '\n' + org.phonesecondary

        address = '\n'.join([i.description for i in org.organizationplace_set.all() if i.description])
        worksheet.write(row, 0, org.name)
        worksheet.write(row, 1, phone)
        worksheet.write(row, 2, org.email)
        worksheet.write(row, 3, address)

    row += 2
    # Add some info about where downloaded from, date
    s = "Generated on {} - downloaded from {}".format(datetime.today(), request.META.get('HTTP_REFERER'))
    worksheet.write(row, 0, s)
    # Insert an image.


    workbook.close()

    output.seek(0)
    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=NHDB_contact_list.xlsx"

    return response


def project_table_excel(request):
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)

    sheet = workbook.add_worksheet()
    sheet.write('A9', 'Name')
    sheet.set_column('A:A', 50)
    sheet.set_column('B:B', 30)
    sheet.set_column('C:C', 20)
    sheet.set_column('D:D', 20)
    sheet.set_column('E:E', 50)
    sheet.write('B9', 'Description')
    sheet.write('C9', 'Start Date')
    sheet.write('D9', 'End Date')
    sheet.write('E9', 'Organizations')

    row = 9
    objects = get_project_queryset(request)

    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})

    for obj in objects:
        row += 1
        # Write some numbers, with row/column notation.

        orgs = []
        orgs = '\n'.join([i.name for i in obj.organization.all()])
        sheet.write(row, 0, obj.name)
        sheet.write(row, 1, obj.description)
        if obj.startdate:
            sheet.write(row, 2, obj.startdate, date_format)
        if obj.enddate:
            sheet.write(row, 3, obj.enddate, date_format)
        sheet.write(row, 4, orgs)

    row += 2
    # Add some info about where downloaded from, date
    s = "Generated on {} - downloaded from {}".format(datetime.today(), request.META.get('HTTP_REFERER'))
    sheet.write(row, 0, s)
    # Insert an image.
    sheet.insert_image('A1', '/webapps/project/media/banner.jpg', options={'x_scale': 0.25, 'y_scale': 0.25})

    workbook.close()

    output.seek(0)
    response = HttpResponse(output.read(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=NHDB_contact_list.xlsx"

    return response


class OrganizationList(SingleTableView):
    model = Organization
    table_class = OrganizationTable

    # paginate_by = 10

    def get_context_data(self, **kwargs):

        context = super(OrganizationList, self).get_context_data(**kwargs)
        context['propertytag_root_nodes'] = PropertyTag.get_root_nodes()

        context['filters'] = {
            'inv': PropertyTag.objects.filter(path__startswith="INV."),
            'act': PropertyTag.objects.filter(path__startswith="ACT."),
            'ben': PropertyTag.objects.filter(path__startswith="BEN."),
            'district': [{'value': 'district.{}'.format(d.path.upper()), 'label': d.name} for d in
                         District.objects.all()],
            'org_location': [{'value': 'org_location.{}'.format(d.path.upper()), 'label': d.name} for d in
                             District.objects.all()],
            'type': [{'value': 'orgtype.{}'.format(o.pk), 'label': o} for o in OrganizationClass.objects.all()]
        }

        if self.request.GET.values() == []:
            context['form'] = OrganizationSearchForm()
        else:
            context['form'] = OrganizationSearchForm(self.request.GET)

        filter_parameter = 'q'
        context['activefilters'] = self.request.GET.getlist(filter_parameter)
        context['dashboard'] = org_dashboard_info(context['object_list'])
        context['object_index'] = json.dumps(object_index(context['object_list']))
        context['object_class_count'] = OrganizationList.model.objects.count()
        return context

    def get_queryset(self):
        return get_organization_queryset(self.request)


def organization_list_as_json(request):
    '''
    Returns Organizations grouped
    :param request:
    :return:
    '''
    organizations, projects = orgset_filter(request)
    return HttpResponse(json.dumps([org.name for org in organizations]), content_type='application/json')


def organizationdescription(request, pk, language_code):
    '''
    Loads a rich text editor to push a description in the selected language as a suggestion to "Suggest.suggest"
    :param UpdateView:
    :return:
    '''
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
    '''
    Loads a rich text editor to push a description in the selected language as a suggestion to "Suggest.suggest"
    :param UpdateView:
    :return:
    '''
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
    #     context['form'] = OrganizationPlaceForm(_data={'organization': organization}, instance = OrganizationPlace.objects.get(pk = form_object_pk))

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
    '''
    Contact list for people in the organization
    :param request:
    :param organization_id:
    :return:
    '''
    organization = Organization.objects.get(pk=organization_id)
    persons = organization.person_set.all()
    context = {'organization': organization, 'persons': persons,
               # 'form': OrganizationAddPersonForm(organization=organization )
                                                }

    return render(request, 'nhdb/organization_persons.html', context)


def thumbnail_image(request):
    '''
    Expects a GET parameter like request=/media/projectimage/100/20150818/star-512_0DXbMiK.jpg
    :param request:
    :return:
    '''
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
        raise AssertionError, _c
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
            if isinstance(content, unicode):
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
            person_list.append(u'{} - {} - {}'.format(person.name, person.contact.email or "No email",
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
            if isinstance(content, unicode):
                row[index] = content.encode('utf-8')

        writer.writerow(row)

    return response


def projectdashboard(request):
    c = {}
    tags = {}
    projects = get_project_queryset(request)
    projectpks = projects.values_list('pk', flat=True)
    propertytags = PropertyTag.objects.select_related('project')

    # Construct a dictionary of tag path, tag name, and project count
    for tag_path, link in (('BEN', 'beneficiary'), ('ACT', 'activity'), ('INV', 'sector')):
        link_name = 'project_' + link
        tag = propertytags.get(path=tag_path)
        filters = {link_name + '__pk__in'.format(link_name): projectpks, 'path__startswith': tag_path + '.'}
        tags[tag.name_en] = list(
            propertytags.filter(**filters).annotate(count=Count(link_name)).values('name', 'path', 'count').order_by(
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
    '''
    Return a JSON-encoded list of places and the number of projects filtered by GET parameters
    :param request:
    :param path:
    :return:
    '''
    path = request.GET.get('path')
    projects = get_project_queryset(request)
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


class ProjectList(SingleTableView):
    model = Project
    table_class = ProjectTable

    def get_context_data(self, **kwargs):

        # Define search parameters
        # Call the base implementation first to get a context
        context = super(ProjectList, self).get_context_data(**kwargs)
        context['searchdescription'] = {}
        search = ''

        # Add in a QuerySet of all the PropertyTags
        context['propertytag_root_nodes'] = PropertyTag.get_root_nodes()
        orgpks = self.request.GET.getlist('organization') or []
        orgpks.extend(self.request.GET.getlist('org'))
        orgpks.extend(self.request.GET.getlist('orgpk'))
        context['organization'] = Organization.objects.filter(pk__in=orgpks)
        c = self.request.GET.copy()
        if 'organization' in c:
            c.pop('organization')
        context['form'] = ProjectSearchForm(c)
        context['count'] = get_project_queryset(self.request).count()

        context['filters'] = {
            'inv': PropertyTag.objects.filter(path__startswith="INV."),
            'act': PropertyTag.objects.filter(path__startswith="ACT."),
            'ben': PropertyTag.objects.filter(path__startswith="BEN."),
            'district': [{'value': 'district.{}'.format(d.path.lower()), 'label': d.name} for d in
                         District.objects.all()],
            'type': [{'value': 'orgtype.{}'.format(o.pk), 'label': o} for o in OrganizationClass.objects.all()],
            'status': [{'value': 'status.{}'.format(o.pk), 'label': o} for o in ProjectStatus.objects.all()],
            'sort': [
                {'value': 'name', 'label': 'Name (A-Z)'},
                {'value': '-name', 'label': 'Name (Z-A)'},
                {'value': 'startdate', 'label': 'Oldest first'},
                {'value': '-startdate', 'label': 'Newest first'},
                {'value': '-enddate', 'label': 'Latest end date first'},

            ]
        }

        filter_parameter = 'q'
        context['activefilters'] = self.request.GET.getlist(filter_parameter)
        context['activeexcludes'] = self.request.GET.getlist('-' + filter_parameter)

        context['searchdescription'] = {}
        # Build a human readable translation of the search filters
        if context['activefilters'] or context['activeexcludes']:
            context['searchdescription'] = {  # List of search parameters in human readable form
                "Sector ": PropertyTag.objects.filter(
                    path__in=[i for i in context['activefilters'] if i.startswith('INV.')]).values_list('name',
                                                                                                        flat=True),
                "NOT Sector ": PropertyTag.objects.filter(
                    path__in=[i for i in context['activeexcludes'] if i.startswith('INV.')]).values_list('name',
                                                                                                         flat=True),
                "Beneficiary ": PropertyTag.objects.filter(
                    path__in=[i for i in context['activefilters'] if i.startswith('BEN.')]).values_list('name',
                                                                                                        flat=True),
                "NOT Beneficiary ": PropertyTag.objects.filter(
                    path__in=[i for i in context['activeexcludes'] if i.startswith('BEN.')]).values_list('name',
                                                                                                         flat=True),
                "Activity ": PropertyTag.objects.filter(
                    path__in=[i for i in context['activefilters'] if i.startswith('ACT.')]).values_list('name',
                                                                                                        flat=True),
                "NOT Activity ": PropertyTag.objects.filter(
                    path__in=[i for i in context['activeexcludes'] if i.startswith('ACT.')]).values_list('name',
                                                                                                         flat=True),
                "In districts": District.objects.filter(
                    path__in=[i.replace('district.', '').upper() for i in context['activefilters'] if
                              i.startswith('district.')]).values_list('name', flat=True),
            }

        status = [i for i in context['activefilters'] if i.startswith('status')]
        if not status:
            context['activefilters'].append('status.A')

        else:
            context['search'] = "All active projects"

        context['searchdescription']['status'] = [i for i in context['activefilters'] if
                                                  i.startswith('status')] or 'Active'
        context['activesort'] = self.request.GET.get('sort')
        context['text'] = self.request.GET.get('text')
        # Edge case where sometimes "None" is taken as literal text
        if not context['text'] or context['text'] == 'None':
            context['text'] = ''

        def timeseries(projects):
            """
            Build a list of tuples of month / number of projects
            :return:
            """
            projects = projects.filter(status_id='A')

            def jstime(dt):
                return (dt - datetime(1970, 1, 1)).total_seconds() * 1000

            dates = []
            for year in range(2010, 2015):

                for month in range(1, 12 + 1):

                    if month == 12:
                        filter = {'startdate__lt': '%s-%s-01' % (year, month),
                                  'enddate__gt': '%s-%s-01' % (year + 1, 1)}
                    else:
                        filter = {'startdate__lt': '%s-%s-01' % (year, month),
                                  'enddate__gt': '%s-%s-01' % (year, month + 1)}
                    t = jstime(datetime(year, month, 1))
                    dates.append((t, projects.filter(**filter).count()))
            return dates

        # context['timeseries'] = json.dumps(timeseries(context['object_list']))

        context['dashboard'] = project_dashboard_info(context['object_list'])

        # Implementing "Next" / "Previous" links for detail

        context['object_index'] = json.dumps(object_index(context['object_list']))
        context['object_class_count'] = ProjectList.model.objects.count()

        return context

    def get_queryset(self):
        # queryset = projectset_filter(self.request)
        queryset = get_project_queryset(self.request)
        # raise AssertionError, queryset
        return queryset


class ProjectSuggestedList(SingleTableView):
    model = Project
    table_class = ProjectTable

    def get_context_data(self, **kwargs):

        # Define search parameters
        # Call the base implementation first to get a context
        context = super(ProjectList, self).get_context_data(**kwargs)

        if self.request.GET.values() == []:
            # ~ raise AssertionError
            context['form'] = ProjectSearchForm(initial={'status': ('A',)})
            return context

        # Add in a QuerySet of all the PropertyTags
        context['propertytag_root_nodes'] = PropertyTag.get_root_nodes()
        context['orgpk'] = self.request.GET.get('organization')
        if context['orgpk']:
            context['organization'] = Organization.objects.get(pk=context['orgpk'])
        c = self.request.GET.copy()
        if 'organization' in c:
            c.pop('organization')
        context['form'] = ProjectSearchForm(c)
        context['count'] = projectset_filter(self.request).count()
        return context

    def get_queryset(self):
        queryset = projectset_filter(self.request)
        # raise AssertionError, queryset
        return queryset


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
        raise TypeError, filtered.query.sql_with_params()

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
        option = {'pk':i.pk, 'name': i.name, 'data-section': data_section, 'data-description': i.description}
        if i.pk in request.GET.getlist('s'):
            option['selected'] = 'selected="selected"'
        else:
            option['selected'] = ''
        s += mark_safe('\n\t<option value="{pk}" data-section="{data-section}" {selected}>{name}</option>'.format(**option))

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
    p = request.GET.get

    template = 'nhdb/crispy_form.html'

    for m in Project, Person, Organization, Suggest, ProjectPerson, ProjectImage, ProjectPlace, ProjectOrganization, OrganizationPlace:
        m_name = m._meta.model_name

        if g(m_name):
            args[m_name] = m.objects.get(pk=g(m_name))

        # Use an underscore to indicate a suggestion ID
        if g('_' + m_name):
            args[m_name] = Suggest.objects.get(pk=g('_' + m_name))

    # if model in args:
    #     args['instance'] = args[model]

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
            args['place'] = AdminArea.objects.get(pk = request.GET.get('place'))
        if request.GET.get('project'):
            args['project'] = Project.objects.get(pk = request.GET.get('project'))

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