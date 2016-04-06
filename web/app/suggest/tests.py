import json
import logging
from django.contrib.auth.models import User
from django.core import serializers
from django.test import TestCase
from nhdb.models import Organization, PropertyTag
from suggest.models import Suggest, AffectedInstance
from suggest import forms
from nhdb.forms import Project, ProjectForm
from django.test.client import Client



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_suggestion(data, code=201, client=None):

    if not client:
        client = Client()
    c = client
    create_post = c.post('/suggest/suggest/', data)

    if create_post.status_code != code:
        raise AssertionError('Expected code %s, got code %s  /n Error message was %s'%(code, create_post.status_code, create_post.content))

    s = Suggest.objects.get(pk = json.loads(create_post.content)['id'])
    assert s.state == 'W'

    for i in s.affectedinstance_set.all():
        logger.info('%s -- %s -- %s -- %s' %(i.model_name, i.suggestion_id, i.model_pk, i.primary))

    return s


def affirm(suggestion,  code=201, client=None):

    if not client:
        client = Client()
    c = client
    r = c.post(suggestion.url, {'_content': suggestion.data, '_content_type': 'application/json'})

    if r.status_code != code:
        logger.error('Expected code %s, got code %s /n Error message was %s', code, r.status_code, r.content)
        raise TypeError('Wrong code received, expected {}; got {}'.format(code, r.status_code))

    if r.status_code != 201:
        return
    # We need to manually set the AffectedInstance pk
    p = suggestion.primary
    p.model_pk =json.loads(r.content)['id']
    p.save()
    # REQUIRED!!! Set this:
    assert suggestion.state == 'A'
    assert suggestion.action == 'CM'
    logger.debug('Returning %s', p.instance)
    return p.instance


class NewProjectTestCase(TestCase):

    def setUp(self):
        s = Suggest.objects.create(
                name='Test case user',
                email='test@josh.com',
                description='Create a New Project',
                user_name='josh',
                user_id=1,
                state='W',
                action='CM',
                is_hidden=False,
                data='{"status": "A", "startdate": "2014-10-01", "enddate": null, "notes_id": null, "description_id": null, "description_pt": null, "stafffulltime": "2", "description_en": "Create monitoring for goverment program and ONG in Municipiu Aileu", "staffparttime": "2", "projecttype": null, "name_tet": null, "name_id": null, "notes_pt": null, "description_tet": null, "notes_tet": null, "name_en": "Advocacy and Monitoring", "name_pt": null, "notes_en": null}',
                url='/rest/nhdb/project',
                method='POST')
        s.affectedinstance_set.add(AffectedInstance(model_name='nhdb_project', model_pk = None, primary=True))
        suggestion_pk = s.pk
        suggestion__pk = '_{}_'.format(s.pk)

        # This second suggestion should alter the project after it has been created
        addOrg = Suggest.objects.create(
                name='josh',
                email='me@testt.com',
                description='Add an organization to this project',
                user_name='josh',
                user_id=1,
                state='W',
                action='CM',
                is_hidden=False,
                method='POST',
                data='{"project": "' + suggestion__pk + '", "organization": "89", "notes": "add Belun", "organizationclass": "P"}',
                url='/rest/nhdb/project/{}/'.format(suggestion__pk)
        )
        addOrg.affectedinstance_set.add(AffectedInstance(model_name='nhdb_organization', model_pk = None, primary=True))
        ai = AffectedInstance(model_name="nhdb_project", model_pk='_{}_')

project_test_data = {
            '_method': 'POST',
            '_url': '/rest/nhdb/project/',
            '_action': 'CM',
            '_description': 'Create a new project in the database',
            '_affected_instance_primary': 'nhdb_project',
            '_next': '/suggest/#object=_suggestion_',
            'name_tet': '',
            'description_tet': '',
            'name_en': 'ttet',
            'description_en': '',
            'name_pt': '',
            'description_pt': '',
            'name_id': '',
            'description_id': '',
            'status': 'A',
            'projecttype': '',
            'startdate': '',
            'enddate': '',
            'stafffulltime': '',
            'staffparttime': '',
            '_name': 'Josh',
            '_email': 'josh.vdbroek@gmail.com',
            '_comment': ''}


class SuggestProjectFormTestCase(TestCase):

    fixtures = ['projectstatus.json','organizationclass', 'projectorganizationclass.json']

    def setUp(self):
        u = User.objects.create_user('josh', 'josh.vdbroek@gmail.com','test')
        u.is_staff = True
        u.save()

    def test_suggestion_update(self):

        c = Client()
        response = c.post('/suggest/suggest/',project_test_data )

        s = Suggest.objects.get(pk = json.loads(response.content)['id'])

        assert int(response.status_code) == 201, 'Response code was %s' % response.status_code
        test_form = ProjectForm(project=s)
        if not isinstance(test_form.get_helper(), forms.UpdateSuggestionHelper):
            msg = 'Expected %s; got %s' % ('UpdateSuggestionHelper', type(test_form.get_helper()))
            raise TypeError(msg)

    def test_suggestion_accept(self):

        c = Client()
        c.login(username='josh', password='test')
        response = c.post('/suggest/suggest/',project_test_data)
        s = Suggest.objects.get(pk = json.loads(response.content)['id'])
        # Generate a 'post' request from the suggestion data
        p = c.post(s.url, {'_content':s.data, '_content_type':'application/json'})
        assert int(p.status_code) == 201, 'Response code was %s' % response.status_code

    def test_new_project_form(self):
        test_form = ProjectForm()
        if not isinstance(test_form.get_helper(), forms.CreateFormHelper):
            msg = 'Expected %s; got %s' % ('CreateFormHelper', type(test_form.get_helper()))
            raise TypeError(msg)

    def test_project_update_form(self):
        p = Project(name="My new project")
        p.save()
        test_form = ProjectForm(project=p)
        if not isinstance(test_form.get_helper(), forms.UpdateFormHelper):
            msg = 'Expected %s; got %s' % ('UpdateFormHelper', type(test_form.get_helper()))
            msg += '\n'
            msg += 'Called ProjectForm with project = %s' % (p)
            raise TypeError(msg)

    def test_suggestion_ForeignKeylink(self):
        """
        Test whether we can retrieve an object instance based on the model name and data parameter
        :return:
        """
        o = Organization(name = "My organization")
        o.save()
        p = Project(name="My new project")
        p.save()
        projectorganization_test_data = {
            '_method': 'POST',
            '_url': '/rest/nhdb/projectorganization/',
            '_action': 'CM',
            '_description': 'Create a new project organization link in the database',
            '_affected_instance_primary': 'nhdb_projectorganization',
            '_next': '/suggest/#object=_suggestion_',
            '_name': 'Josh',
            '_email': 'josh.vdbroek@gmail.com',
            '_comment': '',
            'organization':str(o.pk),
            'project':str(p.pk),
            'organizationclass':'P'
        }
        c = Client()
        response = c.post('/suggest/suggest/', projectorganization_test_data)
        c.login(username='josh', password='test')
        s = Suggest.objects.get(pk = json.loads(response.content)['id'])
        # Generate a 'post' request from the suggestion data

        s.follow('organization')
        s.follow('project')
        s.follow('organizationclass')

        p = c.post(s.url, {'_content':s.data, '_content_type':'application/json'})
        if int(p.status_code) != 201:
            logger.info('Response code was %s', p.status_code)
            logger.info(p.content)

    def test_suggestion_ManyToManyLink(self):

        """
        Test whether we can set up a chained link

        The example here uses a new Beneficiary for FundingOffers
        Before 'Accepting' the beneficiary the FundingOffer should not be acceptable
         After "acceptiny" the FundingOffer should link to the Benefciary
        """

        c = Client()

        def create_organization():
            return create_suggestion(
                {
                    '_method': 'POST',
                    '_url': '/rest/nhdb/organization/',
                    '_action': 'CM',
                    '_description': 'Create a new beneficiary in the database',
                    '_affected_instance_primary': 'nhdb_organization',
                    '_next': '/suggest/#object=_suggestion_',
                    '_name': 'Josh',
                    '_email': 'josh.vdbroek@gmail.com',
                    '_comment': '',
                    'name': 'TEST organization',
                    'orgtype': 'LNGO'
                }
            )

        def create_beneficiary():

            PropertyTag.objects.get_or_create(path='BEN', name='Beneficiary', description='Beneficiary')


            return create_suggestion({
                '_method': 'POST',
                '_url': '/rest/nhdb/propertytag/',
                '_action': 'CM',
                '_description': 'Create a new beneficiary in the database',
                '_affected_instance_primary': 'nhdb_propertytag',
                '_next': '/suggest/#object=_suggestion_',
                '_name': 'Josh',
                '_email': 'josh.vdbroek@gmail.com',
                '_comment': '',
                'path': 'BEN.MUS',
                'name': 'Musical groups',
                'description': 'Musical groups'
            })

        def create_funding_offer(org_suggestion, ben_suggestion):
            return create_suggestion({
                '_method': 'POST',
                '_url': '/rest/donormapping/fundingoffer/',
                '_action': 'CM',
                '_description': 'Create a new Funding Offer in the database',
                '_affected_instance_primary': 'donormapping_fundingoffer',
                '_next': '/suggest/#object=_suggestion_',
                '_name': 'Josh',
                '_email': 'josh.vdbroek@gmail.com',
                '_comment': '',
                'title': 'TEST Funding Offer',
                'organization': '_%s_'%(org_suggestion.pk),
                'amount': 1,
                'description':'Hi',
                'has_many': 'beneficiary',
                'beneficiary':['_%s_'%(ben_suggestion.pk),]
            })

        c.login(username='josh', password='test')
        ben_suggestion = create_beneficiary()
        org_suggestion = create_organization()
        funding_suggestion = create_funding_offer(org_suggestion,ben_suggestion )

        # Trying to "accept"this change should return a 400 code as there are unfinished suggestions first
        affirm(funding_suggestion, code=400, client=c)
        assert isinstance(funding_suggestion.follow('beneficiary')[0], Suggest)
        assert isinstance(funding_suggestion.follow('organization'), Suggest)
        ready, changed, _data = funding_suggestion._set()
        assert ready is False
        assert changed is False

        # After affirming ONE suggestion (this should create a PropertyTag),
        # data should be changed but not ready
        try:
            affirm(ben_suggestion, client=c)
        except:
            logger.error(ben_suggestion.data)
            logger.error(serializers.serialize('json', [ben_suggestion]))

        assert isinstance(funding_suggestion.follow('beneficiary')[0], PropertyTag)
        assert isinstance(funding_suggestion.follow('organization'), Suggest)
        ready, changed, _data = funding_suggestion._set()
        assert ready is False
        assert changed is True
        # This should still get an error as the Organization isn't done yet
        affirm(funding_suggestion, code=400, client=c)

        # Confirm the creationg of the organization
        affirm(org_suggestion, client=c)
        assert isinstance(funding_suggestion.follow('organization'), Organization)
        ready, changed, _data = funding_suggestion._set()
        assert ready is True
        assert changed is True

        # There should be no further changes calling set() a second time, so the second parameter from set()
        # should be False
        ready, changed, _data = funding_suggestion._set()
        assert ready is True
        assert changed is False
        affirm(funding_suggestion, code=201, client=c)