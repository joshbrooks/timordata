import subprocess
import re
import suggest
from crispy_forms.utils import render_crispy_form
from django.contrib.auth.models import User
from django.core.files.temp import NamedTemporaryFile
from django.test import TestCase, Client
from geo.models import World
from library import forms
from library import models

from nhdb.models import Organization, PropertyTag, OrganizationClass
import unicodecsv as csv
from django.core.files import File
import os
import fuzzywuzzy

from suggest.models import Suggest, AffectedInstance
from suggest.tests import create_suggestion, affirm
from unidecode import unidecode
from django.core.files.uploadedfile import SimpleUploadedFile

import logging
import sys
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from belun.tests import logger
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8089'
data_dir = '/home/josh/Desktop/DATA_CENTRE/'


class Fox(object):
    '''
    Fox is an abstraction around Selenium web testing
    '''
    def __init__(self):
        try:
            self.fox = WebDriver()
        except:
            print "No web server detected; skipping web tests"
            self.fox = None

    def login(self, page='/login', name='josh', password='josh', t=5):
        self.get(page)
        WebDriverWait(self.fox, t).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[name=username]'))).send_keys(name)
        WebDriverWait(self.fox, t).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[name=password]'))).send_keys(password)
        WebDriverWait(self.fox, t).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input'))).click()

    def get(self, i):
        return self.fox.get(i)

    def click(self, css, t=5):
        return WebDriverWait(self.fox, t).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).click()

    def clickx(self, xpath, t=5):
        return WebDriverWait(self.fox, t).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()

    def click_last(self, css):
        e = self.fox.find_elements_by_css_selector('.modal-open .btn-primary')[-1]
        return e.click()

    def val(self, css, val, t=5):
        return WebDriverWait(self.fox, t).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).send_keys(val)

    def fill(self, form, field, value):
        css = '#{} [name={}]'.format(form, field)
        return self.val(css, value)

    def form(self, form, values):
        for k, v in values:
            self.fill(form, k, v)

    def wait_for_destroy(self, css, t=5):
        element = self.fox.find_element_by_css_selector(css)
        return WebDriverWait(self.fox, t).until(EC.staleness_of(element))

    def close(self):
        if not self.fox:
            return
        self.fox.quit()


def anti_vowel(text):
    return re.sub("[aeiou]+", "", text)


def version_thumbnail(version):
    if version.upload_en:
        f = NamedTemporaryFile()

        file_path = version.upload_en.path
        subprocess.call(['convert', file_path + '[0]', f.name])
        version.cover_en.save('cover_%s_en' % version.pk, File(f))

        f.close()

    if version.upload_tet:
        f = NamedTemporaryFile()

        file_path = version.upload_tet.path
        subprocess.call(['convert', file_path + '[0]', f.name])
        version.cover_tet.save('cover_%s_tet' % version.pk, File(f))

        f.close()

    if version.upload_pt:
        f = NamedTemporaryFile()

        file_path = version.upload_pt.path
        subprocess.call(['convert', file_path + '[0]', f.name])
        version.cover_pt.save('cover_%s_pt' % version.pk, File(f))

        f.close()


class FoxCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(FoxCase, cls).setUpClass()
        try:
            cls.fox = Fox()
        except RuntimeError:
            cls.fox = None
            return
        u = User.objects.create_user('josh', 'josh.vdbroek@gmail.com','test')
        u.is_staff = True
        u.save()

    @classmethod
    def tearDownClass(cls):
        cls.fox.close()


class SeleniumPublicationInteractionTestCase(FoxCase):
    fixtures = ['library_testing.json']

    def test_go_to_publication(self):

        def add_author(names):
            if not self.fox:
                return
            fox = self.fox

            x = 'author'
            css_author = '[data-modalurl="/library/form/publication/{}/?publication=1"]'.format(x)
            add_author = '[href="/library/form/{}/main"]'.format(x)
            modal_close = '[data-fromurl="/library/form/{}/main/"]'.format(x)
            parent_modal_close = '[data-fromurl="/library/form/publication/{}/?publication=1"]'.format(x)

            fox.get('%s%s' % (self.live_server_url, '/library/publication/#object=1'))

            fox.click(css_author)
            if isinstance(names, basestring):
                names = [names]
            for name in names:
                fox.click(add_author)
                fox.form('author-form', (('name', name), ('displayname', name)))
                fox.click(modal_close)
                fox.wait_for_destroy('[data-fromurl="/library/form/author/main/"]')
            fox.click(parent_modal_close)

        def add_organization(names):
            if not self.fox:
                return
            fox = self.fox

            x = 'organization'

            css_author = '[data-modalurl="/library/form/publication/{}/?publication=1"]'.format(x)
            add_author = '[href="/nhdb/form/{}/main"]'.format(x)
            modal_close = '[data-fromurl="/nhdb/form/{}/main/"]'.format(x)
            parent_modal_close = '[data-fromurl="/library/form/publication/{}/?publication=1"]'.format(x)

            fox.get('%s%s' % (self.live_server_url, '/library/publication/#object=1'))

            fox.click(css_author)

            # Load the nearest
            # val('#div_id_organization .select2-search__field', 'bel')

            if isinstance(names, basestring):
                names = [names]
            for name in names:
                fox.click(add_author)
                fox.form('author-form', (('name', name), ('displayname', name)))
                fox.click(modal_close)
                fox.wait_for_destroy('[data-fromurl="/library/form/author/main/"]')
            fox.click(parent_modal_close)

        add_author(['Joshua Brooks', 'New Author'])



class VersionThumbnailsTestCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(VersionThumbnailsTestCase, cls).setUpClass()
        cls.selenium = WebDriver()
        u = User.objects.create_user('josh', 'josh.vdbroek@gmail.com','test')
        u.is_staff = True
        u.save()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(VersionThumbnailsTestCase, cls).tearDownClass()

    def testVersionThumbnail(self):
        v = models.Version(
            publication = models.Publication.objects.create(
                    name = 'test', pubtype = models.Pubtype.objects.create(
                            code='RPT', name="Report")
            ),
            upload_en = File(file('/home/josh/Documents/test.png')),
            upload_tet = File(file('/home/josh/Documents/test.png')),
            cover_pt = File(file('/home/josh/Documents/test.png'))
        )
        v.save()

        def click(css):
            return WebDriverWait(fox, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).click()

        def click_last(css):
            e = fox.find_elements_by_css_selector('.modal-open .btn-primary')[-1]
            return e.click()

        def val(css, val):
            return WebDriverWait(fox, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).send_keys(val)

        def fill(form, field, value):
            css = '#{} [name={}'.format(form, field)
            return val(css, value)

        # Test a few of the generated thumbnail in a live server
        fox = self.selenium
        fox.get('%s%s' % (self.live_server_url, '/library/version/thumbnail/{}/tet?res=500'.format(v.pk)))
        fox.get('%s%s' % (self.live_server_url, '/library/version/thumbnail/{}/pt?res=300'.format(v.pk)))
        fox.get('%s%s' % (self.live_server_url, '/library/version/thumbnail/{}/en?res=1000'.format(v.pk)))
        fox.close()


class FormsTestCase(TestCase):

    def setUp(self):
        oc = OrganizationClass.objects.create(code="LNGO", orgtype="Local NGO")
        OrganizationClass.objects.create(code="UNKN", orgtype="Unknown")
        Organization.objects.create(name="Belun", orgtype=oc)
        PropertyTag.objects.create(path="INV", name="Sector")
        PropertyTag.objects.create(path="INV.SEC", name="Security")
        World.objects.create(name="Timor Leste", iso3="TLS").save()

        u = User.objects.create_user('josh', 'josh.vdbroek@gmail.com','test')
        u.is_staff = True
        u.save()

    def test_pubtype(self):
        c = Client()
        c.login(username='josh', password='test')
        render_crispy_form(forms.PubtypeForm())
        affirm(create_suggestion(data={
            'code':'RPT',
            'name':'Report'
        }), client=c)

    def test_searchform(self):
        render_crispy_form(forms.PublicationSearchForm())

    def test_PublicationDeleteForm(self):
        # with self.assertRaises(TypeError):
        #     f = PublicationDeleteForm()

        publication = models.Publication.objects.create(
                name='Test',
                pubtype=models.Pubtype.objects.create(
                        code="REP",
                        name="Report")
        )

        f = forms.PublicationDeleteForm(publication=publication)
        assert isinstance(f.helper, suggest.forms.DeleteFormHelper)
        render_crispy_form(f)

    def test_PublicationOrganizationForm(self):
        with self.assertRaises(TypeError):
            forms.PublicationOrganizationForm()

    def test_publication_forms(self):
        # Publication form
        forms.PublicationForm()
        f = forms.PublicationForm(publication=None)
        assert f.helper
        render_crispy_form(f)

    def test_publication_form_existing_publication(self):
        f = forms.PublicationForm(publication=models.Publication.objects.first())
        assert f.helper
        render_crispy_form(f)

    def test_author_form(self):
        f = forms.AuthorForm(author=None)
        assert f.helper
        render_crispy_form(f)

    def test_existing_author_form(self):
        f = forms.AuthorForm(author=models.Author.objects.create(name='Joshua', displayname='Joshua Brooks'))
        assert f.helper
        render_crispy_form(f)

    def test_version_form(self):
        # Check that won't work without publication or existing version
        with self.assertRaises(AssertionError):
            f = forms.VersionForm()

        f = forms.VersionForm(publication=models.Publication.objects.create(
                name='Test',
                pubtype=models.Pubtype.objects.create(
                        code="REP",
                        name="Report")
        )
        )
        assert f.helper
        render_crispy_form(f)

    def test_publicationauthor_form_with_publication(self):

        f = forms.PublicationAuthorForm(publication = models.Publication.objects.create(
                name='Test publication',
                pubtype=models.Pubtype.objects.create(
                    code="REP",
                    name="Report")
        )
        )
        assert f.helper
        render_crispy_form(f)

    def test_version_form_existing_publication(self):
        with self.assertRaises(AssertionError):
            f = forms.VersionForm(publication=None)

        v = models.Version.objects.create(
                publication=models.Publication.objects.create(
                        name='Test',
                        pubtype=models.Pubtype.objects.create(
                                code="REP",
                                name="Report")
                ), description='Test'
        )

        f = forms.VersionForm(version=v)
        assert f.helper
        render_crispy_form(f)

    def test_add_author_suggestion(self):

        v = models.Version.objects.create(
                publication=models.Publication.objects.create(
                        name='Test',
                        pubtype=models.Pubtype.objects.create(
                                code="REP",
                                name="Report")
                ), description='Test'
        )

        p = v.publication

        p.author.add(models.Author.objects.create(name="Josh", displayname="Josh"))
        submission = {
            '_url':'/rest/library/author/',
            '_action':'CM',
            '_description':'Create a new author in the database',
            '_affected_instance_primary':'library_author',
            '__formtype':'Create Form',
            '_next':'/suggest/#object=_suggestion_',
            'name':'New Author',
            'displayname':'Author, New',
            '_name':'Josh',
            '_email':'josh.vdbroek@gmail.com',
            '_comment':''}

        suggest = create_suggestion(submission)
        
        suggest_another = create_suggestion({
            '_method':'PATCH',
            '_url':'/rest/library/publication/%s/'%(p.pk),
            '_action':'UM',
            '_description':'Modify a publication (%s) in the database'%(p),
            '__formtype':'Update Form',
            'has_many':('organization','author','country','location'),
            '_affected_instance_primary':'library_publication %s'%(p.pk),
            'author':('13','_%s_'%(suggest.pk),),
            '_name':'Josh',
            '_email':'josh.vdbroek@gmail.com',
            '_comment':''})

        # Fire off a Suggestion for a new Author


class PublicationAuthorTestCase(TestCase):
    '''
    Check the creation and modification of a Publication Suggestion
    '''
    def test_suggested_publication_forms(self):
        from library.forms import PublicationOrganizationForm, PublicationForm, PublicationAuthorForm
        s = Suggest(
            data = '{"description_id": null, "description_tet": null, "year": "2015", "description_en": null, "pubtype": "BK", "name_tet": null, "name_id": null, "description_pt": null, "name_en": "The Alo Release", "name_pt": null}',
            url = "/rest/library/publication/"  # Django-REST API URL to push the change to when it's approved
            )
        s.skip_signal=True
        s.save()
        AffectedInstance.objects.create(model_name = 'library_publication', primary=True, suggestion=s)
        with open('/tmp/library.tests.PublicationAuthorTestCase.test_suggested_publication_forms.html', 'w') as f:
            f.write('''
            <html><head>
                <script src="/webapps/project/static/jquery.js"></script>
                <script src="/webapps/project/static/bootstrap/js/bootstrap.min.js"></script>
                <link href="/webapps/project/static//bootstrap/css/bootstrap.min.css" rel="stylesheet">
                </head>
                <body>
                ''')
            f.write(render_crispy_form(PublicationForm(publication=s)))
            f.write(render_crispy_form(PublicationAuthorForm(publication=s)))
            f.write(render_crispy_form(PublicationOrganizationForm(publication=s)))
            f.write('</body></html>')

# --- Obsolete tests



class PublicationImportTestCase():
    def setUp(self):
        oc = OrganizationClass.objects.create(code="LNGO", orgtype="Local NGO")
        OrganizationClass.objects.create(code="UNKN", orgtype="Unknown")
        Organization.objects.create(name="Belun", orgtype=oc)
        PropertyTag.objects.create(path="INV", name="Sector")
        PropertyTag.objects.create(path="INV.SEC", name="Security")
        World.objects.create(name="Timor Leste", iso3="TLS").save()
        models.Pubtype.objects.create(code="REP", name="Report")

    def test_import_sitrep(self):

        source_directory = os.path.join(data_dir, 'Belun', 'Situation Review')
        source_file = os.path.join(source_directory, 'situation_review.csv')

        ewer_pub = models.Publication.objects.get_or_create(
                name="ATRES/EWER",
                name_en="Belun EWER situation review",
                name_tet="ATRES Revista Situasaun",
                pubtype=models.Pubtype.objects.get(name="Report"),
                year=0
        )[0]

        ewer_pub.sector.add(PropertyTag.objects.get(name="Security"))
        ewer_pub.organization.add(Organization.objects.get_or_create(name="Belun")[0])
        ewer_pub.author.add(models.Author.objects.get_or_create(name="Belun")[0])
        ewer_pub.country.add(World.objects.get(iso3="TLS"))

        reader = csv.DictReader(open(source_file, 'r'))

        for r in reader:
            print r
            version = {
                'title_en': r['title_en'],
                'title_tet': r['title_tet'],
                'publication_id': ewer_pub.pk
            }

            v = models.Version.objects.create(**version)

            if r['upload_en']:
                file_en = File(open(os.path.join(source_directory, r['upload_en'] + '.pdf'), 'rb'))
                v.upload_en.save(r['upload_en'] + '.pdf', file_en, save=True)
            if r['upload_tet']:
                file_tet = File(open(os.path.join(source_directory, r['upload_tet'] + '.pdf'), 'rb'))
                v.upload_tet.save(r['upload_tet'] + '.pdf', file_tet, save=True)

            for tag_text in [i.strip().lower() for i in r['tags'].split(',')]:
                v.tag.add(models.Tag.objects.get_or_create(name=tag_text)[0])

            print version

    def test_import_trirep(self):

        trimester_report_publication = models.Publication.objects.get_or_create(
                name="ATRES/EWER",
                name_en="Belun Trimester Report",
                name_tet="Relatoriu Trimestral",
                pubtype=models.Pubtype.objects.get(name="Report"),
                year=0
        )[0]

        trimester_report_publication.sector.add(PropertyTag.objects.get(name="Security"))
        trimester_report_publication.organization.add(Organization.objects.get_or_create(name="Belun")[0])
        trimester_report_publication.author.add(models.Author.objects.get_or_create(name="Belun")[0])
        trimester_report_publication.country.add(World.objects.get(iso3="TLS"))

        source_directory = os.path.join(data_dir, 'Belun', 'Trimester Report')
        source_file = os.path.join(source_directory, 'trimester_report.csv')

        reader = csv.DictReader(open(source_file, 'r'))

        for r in reader:
            print r
            version = {
                'title_en': r['title_en'],
                'title_tet': r['title_tet'],
                'publication_id': trimester_report_publication.pk
            }

            v = models.Version.objects.create(**version)

            if r['upload_en']:
                file_en = File(open(os.path.join(source_directory, r['upload_en'] + '.pdf'), 'rb'))
                v.upload_en.save(r['upload_en'] + '.pdf', file_en, save=True)
            if r['upload_tet']:
                file_tet = File(open(os.path.join(source_directory, r['upload_tet'] + '.pdf'), 'rb'))
                v.upload_tet.save(r['upload_tet'] + '.pdf', file_tet, save=True)

            for tag_text in [i.strip().lower() for i in r['tags'].split(',')]:
                v.tag.add(models.Tag.objects.get_or_create(name=tag_text)[0])

            v.save()
            version_thumbnail(v)

    def test_import_brief(self):

        source_directory = os.path.join(data_dir, 'Belun', 'Policy brief')
        source_file = os.path.join(source_directory, 'policy_brief.csv')

        reader = csv.DictReader(open(source_file, 'r'))

        for r in reader:

            policybrief = models.Publication.objects.get_or_create(
                    name="Policy Brief",
                    name_en=r['title_en'],
                    name_tet=r['title_tet'],
                    pubtype=models.Pubtype.objects.get(name="Report")
            )[0]

            policybrief.sector.add(PropertyTag.objects.get(name="Security"))
            policybrief.organization.add(Organization.objects.get_or_create(name="Belun")[0])

            for i in [i.strip() for i in r['org'].split(',')]:
                try:
                    policybrief.organization.add(Organization.objects.get(name=i))
                except Organization.DoesNotExist:
                    policybrief.organization.add(Organization.objects.create(name=i, orgtype_id="UNKN"))

            policybrief.author.add(models.Author.objects.get_or_create(name="Belun")[0])
            policybrief.country.add(World.objects.get(iso3="TLS"))

            version = {
                'title_en': r['title_en'],
                'title_tet': r['title_tet'],
                'publication_id': policybrief.pk
            }

            v = models.Version.objects.create(**version)

            if r['upload_en']:
                file_en = File(open(os.path.join(source_directory, r['upload_en'] + '.pdf'), 'rb'))
                v.upload_en.save(r['upload_en'] + '.pdf', file_en, save=True)
            if r['upload_tet']:
                file_tet = File(open(os.path.join(source_directory, r['upload_tet'] + '.pdf'), 'rb'))
                v.upload_tet.save(r['upload_tet'] + '.pdf', file_tet, save=True)

            for tag_text in [i.strip().lower() for i in r['tags'].split(',')]:
                v.tag.add(models.Tag.objects.get_or_create(name=tag_text)[0])

    def test_import_taf(self):

        # Treat these as separate Publication - Version.

        source_directory = os.path.join(data_dir, 'TAF')
        source_file = os.path.join(source_directory, 'taf.csv')
        reader = csv.DictReader(open(source_file, 'r'))
        for r in reader:
            title = ''
            if r['title_en']:
                title = r['title_en']
            elif r['title_tet']:
                title = r['title_tet']

            pubtype = models.Pubtype.objects.get_or_create(code=anti_vowel(r['type']).upper()[0:3], name=r['type'])[0]
            publication = models.Publication.objects.get_or_create(
                    name=title,
                    name_en=r['title_en'],
                    name_tet=r['title_tet'],
                    name_pt=r['title_pt'],
                    pubtype=pubtype
            )[0]

            version = {
                'title_en': r['title_en'],
                'title_tet': r['title_tet'],
                'publication_id': publication.pk
            }

            v = models.Version.objects.create(**version)

            if r['upload_en']:
                file_en = File(open(os.path.join(source_directory, u'{}.pdf'.format(r['upload_en'])), 'rb'))
                v.upload_en.save(r['upload_en'] + '.pdf', file_en, save=True)
            if r['upload_tet']:
                file_tet = File(open(os.path.join(source_directory, u'{}.pdf'.format(r['upload_tet'])), 'rb'))
                v.upload_tet.save(r['upload_tet'] + '.pdf', file_tet, save=True)
            if r['upload_pt']:
                filename_pt = os.path.join(source_directory, r['upload_pt'] + '.pdf')
                file_pt = File(open(filename_pt), 'rb')
                v.upload_pt.save(r['upload_pt'] + '.pdf', file_pt, save=True)

            for tag_text in [i.strip().lower() for i in r['tags'].split(',')]:
                v.tag.add(models.Tag.objects.get_or_create(name=tag_text)[0])

    def XXX_test_import_UN(self):
        # Folder structure here is more complex than Belun or TAF
        # Also many more files and less "clean"data is going to make this a challenge
        # Hash filename : location

        # NOTE - this is now obsolete

        languages = ['en', 'tet', 'pt']

        hash = {}

        def hash_file_names(data_dir):
            for r, d, f in os.walk(data_dir):
                for filename in f:
                    if filename.endswith('.pdf'):
                        hash[filename] = os.path.join(r, filename)
            return hash

        file_names = hash_file_names(os.path.join(data_dir, 'UN'))
        titles_matched = []

        successes = []
        no_match = []

        titles_matched = []

        source_directory = os.path.join(data_dir, 'UN')
        source_file = os.path.join(source_directory, 'un_sheet_all.csv')
        reader = csv.DictReader(open(source_file, 'r'))

        w = csv.DictWriter(open(os.path.join(source_directory, 'un_sheet_output.csv'), 'w'), reader.fieldnames)
        # First round: an EXACT match

        for r in reader:
            for language in languages:
                upload = 'upload_' + language
                title = 'title_' + language
                filename = None
                if r[upload]:
                    r[upload] = r[upload].strip()

                    file_search_name = r[upload] + '.pdf'
                    filename = file_names.get(file_search_name)
                    if filename:
                        r[upload] = filename
                        file_names.pop(file_search_name)
                        w.writerow(r)
                        titles_matched.append(r[title])
                        continue
                    # Otherwise ratio match closest filename
                    ratio = 0
                    filename = None
                    for i in file_names:
                        _ratio = fuzzywuzzy.fuzz.token_set_ratio(unidecode(i), unidecode(file_search_name))

                        if _ratio > ratio and _ratio > 80:
                            ratio = _ratio
                            filename = i
                    if filename:
                        r[upload] = file_names[filename]
                        file_names.pop(filename)
                        w.writerow(r)

        # Reset and try to find files which match titles from the remaining file_names
        reader = csv.DictReader(open(source_file, 'r'))

        for r in reader:
            for language in languages:
                title = 'title_' + language
                upload = 'upload_' + language
                if r[title]:
                    ratio = 0
                    filename = ''
                    for i in file_names:
                        _ratio = fuzzywuzzy.fuzz.ratio(unidecode(i), unidecode(r[title]))
                        if _ratio > ratio and _ratio > 80:
                            ratio = _ratio
                            filename = i
                    if filename:
                        r[upload] = file_names[filename]
                        file_names.pop(filename)
                        w.writerow(r)
                        titles_matched.append(r[title])

        # This still leaves us with 49 "No Match" documents.
        # Try matching organization name and year and title to file name.
        reader = csv.DictReader(open(source_file, 'r'))

        titles_unmatched = []

        for r in reader:
            for language in languages:
                title = 'title_' + language
                upload = 'upload_' + language
                if r[title]:
                    ratio = 0
                    filename = ''

                    search_string = u"{} {} {}".format(r['org'], r['year'], unidecode(r[title]))

                    for i in file_names:
                        _ratio = fuzzywuzzy.fuzz.token_sort_ratio(unidecode(i), search_string)

                        if _ratio > ratio and _ratio > 79:
                            ratio = _ratio
                            filename = i
                    if filename:
                        r[upload] = file_names[filename]
                        file_names.pop(filename)
                        w.writerow(r)
                        titles_matched.append(r[title])

                    else:
                        if r[title] not in titles_matched:
                            r[upload] = '?'

        print len(successes)

        print len(no_match)

        print len(file_names)

        print file_names
        print titles_unmatched

        for i in file_names:
            os.symlink(file_names[i], os.path.join(data_dir, 'UN', 'no_match', i))

            w.writerow({'upload_en': file_names[i]})

    def test_import_UN(self):
        source_directory = os.path.join(data_dir, 'UN')
        source_file = os.path.join(source_directory, 'un_sheet_output.csv')
        reader = csv.DictReader(open(source_file, 'r'))

        for r in reader:

            pubtype = models.Pubtype.objects.get_or_create(code=anti_vowel(r['type']).upper()[0:3], name=r['type'])[0]
            publication = models.Publication.objects.get_or_create(
                    name=r['title_en'] or r['title_tet'] or r['title_pt'],
                    name_en=r['title_en'],
                    name_tet=r['title_tet'],
                    name_pt=r['title_pt'],
                    pubtype=pubtype
            )[0]

            version = {
                'title_en': r['title_en'],
                'title_tet': r['title_tet'],
                'publication_id': publication.pk
            }

            v = models.Version.objects.create(**version)

            for i in r['author'].split(','):
                publication.author.add(models.Author.objects.get_or_create(name=i)[0])
            for i in r['org'].split(','):
                try:
                    publication.organization.add(Organization.objects.get(name=i))
                except Organization.DoesNotExist:
                    publication.organization.add(Organization.objects.create(name=i, orgtype_id='UNKN'))

            for tag_text in [i.strip().lower() for i in r['tags'].split(',')]:
                v.tag.add(models.Tag.objects.get_or_create(name=tag_text)[0])

            for code in ['en', 'tet', 'pt']:

                if r['upload_en']:
                    file_en = File(open(r['upload_en']), 'rb')
                    v.upload_en.save(r['upload_en'] + '.pdf', file_en, save=True)
                if r['upload_tet']:
                    file_tet = File(open(r['upload_tet']))
                    v.upload_tet.save(r['upload_tet'] + '.pdf', file_tet, save=True)
                if r['upload_pt']:
                    file_pt = File(open(r['upload_pt']))
                    v.upload_pt.save(r['upload_pt'] + '.pdf', file_pt, save=True)

    def test_import_hak(self):

        source_directory = os.path.join(data_dir, 'Asosiasaun HAK')
        source_file = os.path.join(source_directory, 'hak.csv')
        reader = csv.DictReader(open(source_file, 'r'))

        for r in reader:

            pubtype = models.Pubtype.objects.get_or_create(code=anti_vowel(r['type']).upper()[0:3], name=r['type'])[0]
            publication = models.Publication.objects.get_or_create(
                    name=r['title_en'] or r['title_tet'] or r['title_pt'],
                    name_en=r['title_en'],
                    name_tet=r['title_tet'],
                    name_pt=r['title_pt'],
                    pubtype=pubtype
            )[0]

            version = {
                'title_en': r['title_en'],
                'title_tet': r['title_tet'],
                'publication_id': publication.pk
            }

            v = models.Version.objects.create(**version)

            for i in r['author'].split(','):
                publication.author.add(models.Author.objects.get_or_create(name=i)[0])
            for i in r['org'].split(','):
                try:
                    publication.organization.add(Organization.objects.get(name=i))
                except Organization.DoesNotExist:
                    publication.organization.add(Organization.objects.create(name=i, orgtype_id='UNKN'))

            if r['upload_en']:
                file_en = File(open(os.path.join(source_directory, r['upload_en']) + '.pdf'), 'rb')
                v.upload_en.save(r['upload_en'] + '.pdf', file_en, save=True)
            if r['upload_tet']:
                file_tet = File(open(os.path.join(source_directory, r['upload_tet']) + '.pdf'), 'rb')
                v.upload_tet.save(r['upload_tet'] + '.pdf', file_tet, save=True)
            if r['upload_pt']:
                file_pt = File(open(os.path.join(source_directory, r['upload_pt']) + '.pdf'), 'rb')
                v.upload_pt.save(r['upload_pt'] + '.pdf', file_pt, save=True)

            for tag_text in [i.strip().lower() for i in r['tags'].split(',')]:
                v.tag.add(models.Tag.objects.get_or_create(name=tag_text)[0])
            v.save()
            version_thumbnail(v)

    def test_import_FM(self):

        source_file = os.path.join(data_dir, 'fm.csv')
        reader = csv.DictReader(open(source_file, 'r'))

        pubtype = models.Pubtype.objects.get_or_create(code=anti_vowel('Blog').upper()[0:3], name='Blog')[0]

        for year in [2009, 2010, 2011, 2012, 2013, 2014]:
            blog = models.Publication(
                    name="Fundasaun Mahein blogs (%s)" % year,
                    pubtype=pubtype,
                    year=year)
            blog.save()
            blog.sector.add(PropertyTag.objects.get(name="Security"))
            blog.organization.add(Organization.objects.get_or_create(name="Fundasaun Mahein", orgtype_id="UNKN")[0])

        for r in reader:

            publication = models.Publication.objects.get(name="Fundasaun Mahein blogs (%s)" % r['year'])

            version = {
                'title': r['title_tet'],
                'title_tet': r['title_tet'],
                'publication_id': publication.pk
            }

            v = models.Version(**version)
            v.save()

            for tag_text in [i.strip().lower() for i in r['tags'].split(',')]:
                v.tag.add(models.Tag.objects.get_or_create(name=tag_text)[0])

            for tag_text in [i.strip().lower() for i in r['tags_more']]:
                v.tag.add(models.Tag.objects.get_or_create(name=tag_text)[0])

            v.sector.add(PropertyTag.objects.get(path="INV.SEC"))
            v.url = r['url']
            v.save()

            print v

