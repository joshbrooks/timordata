import json

import logging, sys

from crispy_forms.utils import render_crispy_form
from django.contrib.auth.models import User
from django.test import TestCase
from nhdb.forms_delete import OrganizationDeleteForm
from suggest.models import Suggest, AffectedInstance
# Create your tests here.
from suggest import forms
from nhdb.forms import Project, ProjectForm, OrganizationForm, OrganizationDescriptionForm, ProjectpropertiesForm, \
    ProjectTypeForm
from nhdb.models import Organization, OrganizationClass, ProjectType, ProjectImage
import unittest
from django.test.client import Client
from suggest.tests import affirm, create_suggestion
from django.core.files import File
from library.tests import FoxCase
logger = logging.getLogger('nhdb.tests')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stderr))

html_output_test = '/webapps/project/belun/nhdb/test_outputs/tests'


def header(text):
    return '<h4>%s</h4>' % text


def serialize_to_post(text):
    d = {}
    for i in json.loads(text):
        d[i['name']] = i['value']
    return d

serialized_organization_suggestion = '[{"name":"csrfmiddlewaretoken","value":"0dc9Yijn1WVElLGDW2DvT79ir0X9Gbtt"},{"name":"_method","value":"POST"},{"name":"_url","value":"/rest/nhdb/organization/"},{"name":"_action","value":"CM"},{"name":"_description","value":"Create a new organization in the database"},{"name":"_affected_instance_primary","value":"nhdb_organization"},{"name":"__formtype","value":"Create Form"},{"name":"_next","value":"/suggest/#object=_suggestion_"},{"name":"name","value":"My Organization"},{"name":"orgtype","value":"LNGO"},{"name":"stafffulltime","value":""},{"name":"staffparttime","value":""},{"name":"_name","value":"Josh"},{"name":"_email","value":"josh.vdbroek@gmail.com"},{"name":"_comment","value":""}]'


class ProjectImageThumbnails(TestCase):

    def test_projectimage(self):
        '''
        Thumbnail class for ProjectImage
        '''

        i = ProjectImage.objects.create(
            image=File(file('/home/josh/Documents/test.png')),
            project=Project.objects.create(name="Test Project")
        )

        i.thumbnail()


class ProjectTestCase(FoxCase):
    '''
    Selenium testing
    '''

    def setUp(self):
        ProjectType.objects.create(
            description='Active'
        )

    def test_project_suggest(self):
        fox = self.fox
        self.fox.get(self.live_server_url+'/nhdb/project')
        fox.clickx("//*[contains(text(), 'Management')]")
        fox.click('[data-modalurl="/nhdb/form/project/main/"]')
        fox.click('#english')
        fox.form('project-form', (('name_en', 'National Database Project'),('description_en', 'Providing information about NGOs and projects in Timor')))
        fox.click('button[data-fromurl="/nhdb/form/project/main/"]')
        fox.get(self.live_server_url+'/suggest/?state=W')
        fox.login()
        fox.get(self.live_server_url+'/suggest/?state=W')
        fox.click('form.restInteraction .btn-primary')
        fox.get(self.live_server_url+'/nhdb/project/?object=1')


class SuggestOrganizationFormTestCase(TestCase):

    fixtures = ['organizationclass.json', 'organizations_10.json', 'projecttype', 'projectstatus', 'project_100', 'projectproperties']

    @classmethod
    def setUpClass(cls):
        with open(html_output_test, 'w') as o:
            o.write('<html>')
            o.write('<head>')
            o.write('<script src="./bootstrap/js/jquery.js"></script>')
            o.write('<script src="./bootstrap/js/bootstrap.min.js"></script>')
            o.write('<link href="./bootstrap/css/bootstrap.min.css" rel="stylesheet">')
            o.write('<head>')
            o.write('<body>')

    @classmethod
    def tearDownClass(cls):
        with open(html_output_test, 'a') as o:
            o.write('</html></body>')

    def setUp(self):

        u = User.objects.create_user('josh', 'josh.vdbroek@gmail.com','test')
        u.is_staff = True
        u.save()

    def test_organization_form(self):

        f = OrganizationForm()
        with open(html_output_test, 'a') as _test:
            _test.write(header('New Organization Form'))
            _test.write(render_crispy_form(f))

        if not isinstance(f.get_helper(), forms.CreateFormHelper):
            msg = 'Expected %s; got %s' % ('CreateFormHelper', type(f.get_helper()))
            raise TypeError(msg)

    def test_suggestion_update(self):
        '''
        Make a suggestion and ensure that an UpdateSuggestionHelper is attached to the form
        :return:
        '''
        c = Client()
        response = c.post('/suggest/suggest/', serialize_to_post(serialized_organization_suggestion))

        s = Suggest.objects.get(pk = json.loads(response.content)['id'])

        assert int(response.status_code) == 201, 'Response code was %s' % response.status_code
        test_form = OrganizationForm(organization=s)
        with open(html_output_test, 'a') as _test:
            _test.write(header('Change Suggestion Form'))
            _test.write(render_crispy_form(test_form))
        if not isinstance(test_form.get_helper(), forms.UpdateSuggestionHelper):
            msg = 'Expected %s; got %s' % ('UpdateSuggestionHelper', type(test_form.get_helper()))
            raise TypeError(msg)

    def test_organization_update(self):

        f = OrganizationForm(organization = Organization.objects.first())
        with open(html_output_test, 'a') as _test:
            _test.write(header('Update Organization Form'))
            _test.write(render_crispy_form(f))

        if not isinstance(f.get_helper(), forms.UpdateFormHelper):
            msg = 'Expected %s; got %s' % ('UpdateFormHelper', type(f.get_helper()))
            raise TypeError(msg)

    def test_OrganizationDescriptionForm(self):

        f = OrganizationDescriptionForm(organization=Organization.objects.first())
        with open(html_output_test, 'a') as _test:
            _test.write(header('Update Organization Form'))
            _test.write(render_crispy_form(f))

        if not isinstance(f.get_helper(), forms.UpdateFormHelper):
            msg = 'Expected %s; got %s' % ('UpdateFormHelper', type(f.get_helper()))
            raise TypeError(msg)

    def test_ProjectForm(self):

        formclass = ProjectForm
        f = formclass(project=Project.objects.first())
        f.helper
        assert isinstance(f.get_helper(), forms.UpdateFormHelper)
        with open(html_output_test, 'a') as _test:
            _test.write(header('Update a project'))
            _test.write(render_crispy_form(f))

    def test_NewProjectForm(self):

        formclass = ProjectForm
        f = formclass()
        f.helper
        assert isinstance(f.get_helper(), forms.CreateFormHelper)
        with open(html_output_test, 'a') as _test:
            _test.write(header('Create a new project form'))
            _test.write(render_crispy_form(f))

    def test_ProjectPropertiesForm(self):
        formclass = ProjectpropertiesForm
        f = formclass(project=Project.objects.all()[5])
        assert isinstance(f.get_helper(), forms.UpdateFormHelper)
        with open(html_output_test, 'a') as _test:
            _test.write(header('Update project properties form'))
            _test.write(render_crispy_form(f))


class DeleteFormTestCase(TestCase):
    """
    Test the rendering of Delete___Form and
    """
    fixtures = ['organizationclass.json', 'organizations_10.json', 'projecttype', 'projectstatus', 'project_100', 'projectproperties']

    def test_drop_organization(self):
        o = Organization()
        o.name = 'Test'
        o.orgtype = OrganizationClass.objects.first()
        o.save()
        helper = OrganizationDeleteForm(o).helper


class ProjectTypeFormTestCase(TestCase):

    def setUp(self):
        u = User.objects.create_user('josh', 'josh.vdbroek@gmail.com','test')
        u.is_staff = True
        u.save()

    def test_project_type(self):

        formclass = ProjectTypeForm
        f = formclass()
        assert isinstance(f.get_helper(), forms.CreateFormHelper)
        with open(html_output_test, 'a') as _test:
            _test.write(header('Create project type form'))
            _test.write(render_crispy_form(f))

        c = Client()
        c.login(username='josh', password='test')

        affirm(create_suggestion(data = {
            '_method': 'POST',
            '_url': '/rest/nhdb/projecttype/',
            '_action': 'CM',
            '_description': 'test',
            '_affected_instance_primary': 'nhdb_projecttype',
            '_next': '/suggest/#object=_suggestion_',
            '_name': 'Josh',
            '_email': 'josh.vdbroek@gmail.com',
            '_comment': '',
            'description':'Humanitarian'
        }), client = c)

        formclass = ProjectTypeForm
        f = formclass(projecttype=ProjectType.objects.last())
        assert isinstance(f.get_helper(), forms.UpdateFormHelper)
        with open(html_output_test, 'a') as _test:
            _test.write(header('Create project type form'))
            _test.write(render_crispy_form(f))

# class TestFormsAllExist(TestCase):
#
#     def test_all(self):
#         """
#         Check for the existence of a "CreateForm" for every model
#         :return:
#         """
#         from form_present_check import form_present
#         form_present()
#