#!/usr/bin/python
# -*- coding: utf-8 -*-
from tempfile import NamedTemporaryFile
import subprocess
import sys
import logging
import os
import re
import warnings

logging.basicConfig(level=logging.WARN)

os.environ['DJANGO_SETTINGS_MODULE'] = 'belun.settings'
# sys.path.append(os.path.join(os.path.abspath('.'), '../'))

import django

django.setup()

from geo.models import World, AdminArea
from library.models import *
from nhdb.models import Organization, PropertyTag, OrganizationClass
import unicodecsv as csv
from django.core.files import File
# Create your tests here.
import os
import fuzzywuzzy
from unidecode import unidecode

data_dir = '/home/josh/Desktop/DATA_CENTRE/'


def anti_vowel(text):
    return re.sub("[aeiou]+", "", text)


def versions_thumbnail(_format="jpg"):
    for version in Version.objects.all():
        version_thumbnail(version, _format)


def version_thumbnail(version, _format="jpg"):

    for code in ['en', 'tet', 'pt', 'id']:
        upload = getattr(version, 'upload_%s' % (code))
        cover = getattr(version, 'cover_%s' % (code))
        if upload:
            if not os.path.exists(upload.path):
                warnings.warn("Path {} not found!".format(upload.path))
                continue
            cover_file_name = os.path.split(upload.path)[1].replace('pdf', _format)
            if os.path.exists(os.path.join('/webapps/project/media/publication_covers', cover_file_name)):
                setattr(version, 'cover_%s' % (code), '/webapps/project/media/publication_covers/%s' % (cover_file_name))
                version.save()
                continue
            else:
                f = NamedTemporaryFile()
                print(['convert', upload.path + '[0]', _format + ':' + f.name])
                subprocess.call(['convert', upload.path + '[0]', _format + ':' + f.name])
                cover.save(cover_file_name, File(f))
                f.close()


def import_sitrep():
    source_directory = os.path.join(data_dir, 'Belun', 'Situation Review')
    source_file = os.path.join(source_directory, 'situation_review.csv')

    ewer_pub = Publication.objects.get_or_create(
        name="ATRES/EWER",
        name_en="Belun EWER situation review",
        name_tet="ATRES Revista Situasaun",
        pubtype=Pubtype.objects.get(name="Report"),
        year=0
    )[0]

    source_directory = os.path.join(data_dir, 'Belun', 'Situation Review')
    source_file = os.path.join(source_directory, 'situation_review.csv')
    import_generic(source_directory, source_file, absolute_paths=False, master_publication=ewer_pub)
    ewer_pub.country.add(World.objects.get(iso3="TLS"))
    ewer_pub.organization.add(Organization.objects.get(name="Belun"))


def import_trirep():
    p = Publication.objects.get_or_create(
        name="ATRES/EWER",
        name_en="Belun Trimester Report",
        name_tet="Relatoriu Trimestral",
        pubtype=Pubtype.objects.get(name="Report"),
        year=0
    )[0]

    source_directory = os.path.join(data_dir, 'Belun', 'Trimester Report')
    source_file = os.path.join(source_directory, 'trimester_report.csv')
    import_generic(source_directory, source_file, absolute_paths=False, master_publication=p)
    p.country.add(World.objects.get(iso3="TLS"))
    p.organization.add(Organization.objects.get(name="Belun"))


def import_alerts():
    p = Publication.objects.get_or_create(
        name="ATRES/EWER ",
        name_en="Alerts from Early Warning, Early Response (EWER)",
        name_tet="Alerta husi Sistema Atensaun no Responde Sedu (AtRes)",
        pubtype=Pubtype.objects.get(name="Report"),
        year=0
    )[0]

    source_directory = os.path.join(data_dir, 'Belun', 'Alerts')
    source_file = os.path.join(source_directory, 'alerts.csv')

    import_generic(source_directory, source_file, absolute_paths=False, master_publication=p)

    p.country.add(World.objects.get(iso3="TLS"))
    p.organization.add(Organization.objects.get(name="Belun"))


def import_brief():
    source_directory = os.path.join(data_dir, 'Belun', 'Policy brief')
    source_file = os.path.join(source_directory, 'policy_brief.csv')
    p = Publication(
        pubtype=Pubtype.objects.get(name="Report"),
        name_en="Policy brief (EWER)",
        name_tet="Relatoriu politika (AtRes)"
    )
    p.save()
    import_generic(source_directory, source_file, absolute_paths=False, master_publication=p)
    p.country.add(World.objects.get(iso3="TLS"))
    p.organization.add(Organization.objects.get(name="Belun"))


def import_taf():
    # Treat these as separate Publication - Version.
    source_directory = os.path.join(data_dir, 'TAF')
    source_file = os.path.join(source_directory, 'taf.csv')
    import_generic(source_directory, source_file, absolute_paths=False)


def import_un():
    source_directory = os.path.join(data_dir, 'UN')
    source_file = os.path.join(source_directory, 'un_sheet_output.csv')

    import_generic(source_directory, source_file, absolute_paths=True)


def import_hak():
    kw = {
        'source_directory': os.path.join(data_dir, 'Asosiasaun HAK'),
        'source_file': os.path.join(data_dir, 'Asosiasaun HAK', 'hak.csv')
    }

    import_generic(**kw)


def import_generic(source_directory, source_file, absolute_paths=False, master_publication=None, uploadfiles=True):
    """

    :param source_directory: Directory to extract source files from
    :param source_file: Name of the CSV file to read metadata from
    :param absolute_paths: Boolean - True for absolute paths
    :param master_publication: Publication object if this should be treated as ONE publication
    :return:
    """

    logging.info('Importing from CSV file at {}'.format(source_file))

    reader = csv.DictReader(open(source_file, 'r'))

    def create_publication(r):

        pub_kw = {'name': r['title_en'] or r['title_tet'] or r['title_pt']}
        for lang in ['tet', 'en', 'pt']:
            if r.get('title_' + lang, None):
                pub_kw['name_' + lang] = r['title_' + lang]

        if r.get('type', None):
            try:
                pub_kw['pubtype'] = Pubtype.objects.get(name=r['type'])
            except Pubtype.DoesNotExist:
                pub_kw['pubtype'] = Pubtype.objects.create(name=r['type'], code=anti_vowel(r['type']).upper()[0:3])

        else:
            # Assume a pubtype is "Report" if it is not provided or blank
            pub_kw['pubtype'] = Pubtype.objects.get(name='Report')
        try:
            pub_kw['year'] = int(r.get('year', 0))
        except ValueError:
            logging.error('Invalid value for publication year of {}: ( {} )'.format(pub_kw['name'], r.get('year')))

        Publication.objects.filter(**pub_kw).delete()

        publication = Publication.objects.create(**pub_kw)
        logging.info(u'P.{} : {}'.format(publication.pk, publication.name))

        if r.get('author', None):
            for i in [i.strip() for i in r['author'].split(',')]:
                publication.author.add(Author.objects.get_or_create(name=i.strip())[0])

        if r.get('country', None):
            for i in [i.strip() for i in r['country'].split(',')]:
                try:
                    publication.country.add(World.objects.get(name__iexact=i))
                except World.DoesNotExist:
                    try:
                        publication.location.add(AdminArea.objects.get(name__iexact=i))
                    except AdminArea.DoesNotExist:
                        logging.error(u'No Location: {} ( {} )'.format(pub_kw['name'], i))
                    except AdminArea.MultipleObjectsReturned:
                        logging.warn(u'Multiple Location: {} ( {} )'.format(pub_kw['name'], i))
                        for adminarea in AdminArea.objects.filter(name__iexact=i.strip()):
                            publication.location.add(adminarea)

        if r.get('location', None):
            for i in [i.strip() for i in r['location'].split(',')]:
                try:
                    publication.location.add(AdminArea.objects.get(name__iexact=i))
                except AdminArea.DoesNotExist:
                    try:
                        publication.country.add(World.objects.get(name__iexact=i))
                    except World.DoesNotExist:

                        if assists['location'].get(i):
                            publication.location.add(AdminArea.objects.get(path=assists['location'].get(i)))
                        else:
                            logging.error(u'No Location: {} ( {} )'.format(pub_kw['name'], i))
                except AdminArea.MultipleObjectsReturned:
                    logging.warn(u'Multiple Location: {} ( {} )'.format(pub_kw['name'], i))
                    for adminarea in AdminArea.objects.filter(name__iexact=i.strip()):
                        publication.location.add(adminarea)

        if r.get('org', None):
            for i in [i.strip() for i in r['org'].split(',')]:
                assert i in assists['org'].keys()
                
                logging.debug(i)

                if assists['org'].get(i):
                    org_name = assists['org'].get(i)
                else:
                    org_name = i
                    
                try:
                    publication.organization.add(Organization.objects.get(name=org_name))
                    
                except Organization.DoesNotExist:
                    logging.warn(u'Creating a new Organization object: {}'.format(i))
                    publication.organization.add(Organization.objects.create(name=i, orgtype_id='None'))

        publication.save()
        return publication

    def upload_files(r, version, file_paths):

        if not absolute_paths:

            if r.get('upload_en', None):
                file_en = File(open(os.path.join(source_directory, r['upload_en']) + '.pdf'), 'rb')
                version.upload_en.save(r['upload_en'] + '.pdf', file_en, save=True)
            if r.get('upload_tet', None):
                file_tet = File(open(os.path.join(source_directory, r['upload_tet']) + '.pdf'), 'rb')
                version.upload_tet.save(r['upload_tet'] + '.pdf', file_tet, save=True)
            if r.get('upload_pt', None):
                file_pt = File(open(os.path.join(source_directory, r['upload_pt']) + '.pdf'), 'rb')
                version.upload_pt.save(r['upload_pt'] + '.pdf', file_pt, save=True)

        if absolute_paths:

            if r.get('upload_en', None):
                file_en = File(open(r['upload_en']), 'rb')
                v.upload_en.save(r['upload_en'], file_en, save=True)
            if r.get('upload_tet', None):
                file_tet = File(open(r['upload_tet']))
                v.upload_tet.save(r['upload_tet'], file_tet, save=True)
            if r.get('upload_pt', None):
                file_pt = File(open(r['upload_pt']))
                v.upload_pt.save(r['upload_pt'], file_pt, save=True)

    def create_version(r, publication):

        ver_kw = {'publication': p}

        for lang in ['tet', 'en', 'pt']:
            if r.get('title_' + lang, None):
                ver_kw['title_' + lang] = r['title_' + lang]
            if r.get('url', None):
                ver_kw['url'] = r['url']

        version = Version.objects.create(**ver_kw)
        logging.info(u'V.{} : {}'.format(version.pk, version.title))

        for tag_text in [i.strip().lower() for i in r['tags'].split(',')]:

            if len(tag_text) < 3:
                continue

            version_property_tags = PropertyTag.objects.filter(name__iexact=tag_text)

            for version_property_tag in version_property_tags:

                if version_property_tag.path.startswith('BEN'):
                    version.beneficiary.add(version_property_tag)
                elif version_property_tag.path.startswith('ACT'):
                    version.activity.add(version_property_tag)
                elif version_property_tag.path.startswith('INV'):
                    version.sector.add(version_property_tag)

            if not version_property_tags:
                version.tag.add(Tag.objects.get_or_create(name=tag_text)[0])

        version.save()
        return version

    for r in reader:
        p = master_publication
        if not master_publication:
            p = create_publication(r)
        v = create_version(r, p)
        if uploadfiles:
            upload_files(r, v, absolute_paths)


def import_fm():
    source_file = os.path.join(data_dir, 'fm.csv')
    reader = csv.DictReader(open(source_file, 'r'))
    try:
        pubtype = Pubtype.objects.get(name='Blog')
    except Pubtype.DoesNotExist:
        pubtype = Pubtype.objects.get_or_create(code=anti_vowel('Blog').upper()[0:3], name='Blog')[0]

    for year in [2009, 2010, 2011, 2012, 2013, 2014]:
        blog = Publication(
            name="Fundasaun Mahein blogs (%s)" % year,
            pubtype=pubtype,
            year=year)
        blog.save()

        blog.country.add(World.objects.get(iso3="TLS"))
        blog.organization.add(Organization.objects.get(name="Fundasaun Mahein"))

        logging.info('P.{} : {}'.format(blog.pk, blog.name))

    for r in reader:

        publication = Publication.objects.get(name="Fundasaun Mahein blogs (%s)" % r['year'])

        v = {
            # 'title': r['title_tet'],
            'title_tet': r['title_tet'],
            'publication_id': publication.pk,
            'url_tet': r['url'],
        }

        version = Version(**v)
        version.save()
        logging.info(u'V.{} : {}'.format(version.pk, version.title))
        tag_text_strings = [i.strip().lower() for i in r['tags'].split(',')]
        tag_text_strings.extend([i.strip().lower() for i in r['tags_more'].split(',')])

        for tag_text in tag_text_strings:
            if len(tag_text) < 1:
                continue
            version_property_tags = PropertyTag.objects.filter(name__iexact=tag_text)
            logging.info(u'%s' % version_property_tags)

            for version_property_tag in version_property_tags:

                if version_property_tag.path.startswith('BEN'):
                    logging.info(u'Using PROPERTY: %s' % tag_text)
                    version.beneficiary.add(version_property_tag)
                elif version_property_tag.path.startswith('ACT'):
                    logging.info(u'Using PROPERTY: %s' % tag_text)
                    version.activity.add(version_property_tag)
                elif version_property_tag.path.startswith('INV'):
                    logging.info(u'Using PROPERTY: %s' % tag_text)
                    version.sector.add(version_property_tag)

            if not version_property_tags:
                logging.info(u'Using TAG: %s' % tag_text)
                version.tag.add(Tag.objects.get_or_create(name=tag_text)[0])

        version.save()


if __name__ == "__main__":
    # oc, oc_created = OrganizationClass.objects.get_or_create(code="LNGO", orgtype="Local NGO")
    # OrganizationClass.objects.get_or_create(code="UNKN", orgtype="Unknown")
    # Organization.objects.get_or_create(name="Belun", orgtype=oc)

    assists = {'location': {}, 'org': {}}

    for placename, location_pk in csv.reader(open('assist_locations.csv')):
        assists['location'][placename] = location_pk

    for supplied_name, database_name in csv.reader(open('assist_organizations.csv')):
        assists['org'][supplied_name] = database_name

    Tag.objects.all().delete()
    Author.objects.all().delete()
    Publication.objects.all().delete()
    Version.objects.all().delete()

    import_hak()
    import_fm()
    import_taf()
    import_sitrep()
    import_trirep()
    import_alerts()
    import_brief()
    import_un()

    for v in Version.objects.all():
        version_thumbnail(v)
