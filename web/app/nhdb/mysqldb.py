import json
import logging
import sys
import datetime
import unittest
import django
from django.contrib.gis.geos import GEOSGeometry
from django.db import IntegrityError
import os
logging.basicConfig(level=logging.INFO)
# from nmb.NetBIOS import NetBIOS
#
#
# def netbios_to_ip(name='USER-HP'):
#     n = NetBIOS(broadcast=True, listen_port=0)
#     ip = n.queryName(name, timeout=30)
#     return ip
# try:
#     host_ip = netbios_to_ip(name='USER-HP')[0]
#     # host_ip = 'localhost'
# except:
#     logging.warn('No host found at {}. Using {}.'.format('USER-HP', 'localhost'))
#     host_ip='localhost'


os.environ['DJANGO_SETTINGS_MODULE'] = 'belun.settings'
sys.path.append(os.path.join(os.path.abspath('.'), '../'))

django.setup()

from nhdb.models import Organization, OrganizationClass, Project, ProjectStatus, ProjectPlace, \
    ProjectPerson, OrganizationPlace, ProjectOrganizationClass, ProjectOrganization, PropertyTag, Person
from geo.models import AdminArea as Place, AdminArea


import MySQLdb
from mappings import Mapping

m = Mapping()

# New Data to be loaded:
# Target beneficiaries

property_queries = {'projectpartners':"""
SELECT DISTINCT fkProjectId, fkPartnerOrganizationId FROM tblprojectpartners
WHERE fkProjectId IN (SELECT pkProjectId from tblnewprojects)
AND fkPartnerOrganizationId IN (SELECT pkOrganizationId from tblneworganizations);""",
                    'ben':"""
SELECT DISTINCT fkProjectID, fkTargetBeneficiariesId from tblprojecttargetbeneficiaries
where fkProjectID is not null
and fkProjectId in (SELECT pkProjectId from tblnewprojects)
and fkTargetBeneficiariesId is not null
""",
                    'act':
"""
SELECT DISTINCT fkProjectID, fkMainActivitieId from tblprojectmainactivities
where fkProjectID is not null
and fkProjectId in (SELECT pkProjectId from tblnewprojects)
and fkMainActivitieId is not null
""",
                    'inv':"""
select fkProjectId, fkAreaOfInvolvmentsId
from tblprojectareaofinvolvments
where fkProjectId is not null
and fkProjectId in (SELECT pkProjectId from tblnewprojects)
and fkAreaOfInvolvmentsId is not null"""

}

dbsettings = {
    'user': 'root',
    'passwd': 'duck',
    'db': 'development',
    'host': 'source' # host_ip
}

db = MySQLdb.connect(**dbsettings)
c = db.cursor()


def _d(string):
    """
    Returns a string decoded as LATIN-1 to unicode
    or None if original string is null
    """
    if string is None or string == '':
        return None
    else:
        try:
            return string.decode("latin-1").encode("utf-8")
        except Exception, e:
            logging.warn('Ran into a string which could not be handled - {}'.format(string))


def mysql_timestamp_to_date(timestamp):
    """
    Try to convert a mysql timestamp to a date format
    :param timestamp:
    :return:
    """
    if not timestamp:
        return None
    datestring = timestamp.split(' ')[0]

    if '/' in datestring:
        separator = '/'
    elif '-' in datestring:
        separator = '-'
    else:

        logging.warn('Ran into a timestamp which could not be handled - {} has no separator. Blank date returned.'.format(timestamp))
        return None

    dateformat = '%d{0}%m{0}%Y'.format(separator)
    dateformat_ = '%m{0}%d{0}%Y'.format(separator)
    dateformat__ = '%Y{0}%m{0}%d'.format(separator)

    try:
        return datetime.datetime.strptime(datestring, dateformat).date()
    except:
        try:
            return datetime.datetime.strptime(datestring, dateformat_).date()
        except Exception, e:
            try:
                return datetime.datetime.strptime(datestring, dateformat__).date()
            except Exception, e:
                logging.warn('{} Ran into a timestamp which could not be handled - {}. Blank date returned.'.format(e, timestamp))
                return None


def FetchOneAssoc(cursor):
    data = cursor.fetchone()
    if data is None:
        return None
    desc = cursor.description

    dict = {}

    for (name, value) in zip(desc, data):
        dict[name[0]] = value

    return dict


def setup():

    logging.info('Starting setup')

    for key, kw in m.orgtype.items():
        oc, created = OrganizationClass.objects.get_or_create(code=kw['code'])
        if created:
            oc.orgtype = kw.get('orgtype')
            oc.save()

    for key, kw in m.projectstatus.items():
        ps, created = ProjectStatus.objects.get_or_create(code=kw.get('code'))
        if created:
            ps.description = kw.get('description')
            ps.save()

    for key, kw in m.projectorganizationclass.items():
        pc, created = ProjectOrganizationClass.objects.get_or_create(code=kw.get('code'))
        if created:
            pc.description = kw.get('description')
            pc.save()

    # propertytags = json.load(open('fixtures/nhdb_propertytag.json'))

    # for i in propertytags:
    #     d = i['fields']
    #     d['id'] = i['pk']
    #     try:
    #         PropertyTag.objects.get_or_create(**d)
    #     except IntegrityError, e:
    #         logging.warn(e)


def importorganizations():
    Organization.objects.all().delete()
    c.execute("SELECT * FROM tblneworganizations")
    row = FetchOneAssoc(c)
    while row is not None:
        _orgtype = m.orgtype.get(row.get('fkOrgTypeId'), {})
        orgtype = OrganizationClass.objects.get(code=_orgtype.get('code', 'None'))

        try:
            organization, created = Organization.objects.get_or_create(pk=row.get('pkOrganizationId'), orgtype=orgtype)
            organization.pk = row.get('pkOrganizationId')
            organization.name = row.get('name').decode("latin-1").encode("utf-8")
            organization.phoneprimary=row.get('primaryPhone')
            organization.phonesecondary=row.get('secondaryPhone')
            organization.fax=row.get('faxNumber')
            organization.email=row.get('email')
            organization.web=row.get('web')
            organization.facebook=row.get('facebook')
            organization.verified=mysql_timestamp_to_date(row.get('verified'))

            if row.get('OrgStatus') == 2:
                organization.active = False

            organization.save()
        except Exception, e:
            logging.warn("Experienced an error creating Organization /n {}".format(row))
            logging.warn(e)
        row = FetchOneAssoc(c)


def importpersons():

    c.execute("""SELECT pkPersonId, firstName, lastName, concat(firstName,' ',lastName), title, fkOrganizationId, phone, mobilePhone, email, verified from tblpeople WHERE fkOrganizationId IS NOT NULL AND firstName IS NOT NULL;""")

    for pk, first, last, name, title, org_id, phone, mobile, email, verified in c.fetchall():

        try:
            organization_id = Organization.objects.get(pk = org_id)
        except Organization.DoesNotExist:
            organization_id = None

        if phone:

            if mobile:
                phone = mobile+','+phone

        else:

            if mobile:
                phone = mobile

        p, created = Person.objects.get_or_create(pk = pk)
        p.name = _d(name)
        p.first = _d(first)
        p.last = _d(last)
        p.title = _d(title)
        p.phone = phone
        p.email = email
        p.verified = mysql_timestamp_to_date(verified)
        p.organization_id = organization_id
        try:
            p.save()
        except Exception, e:
            logging.warn("Experienced an error creating Person /n {}".format((pk, first, last, name, title, org_id)))
            logging.warn(e)


def importprojects():
    Project.objects.all().delete()

    c.execute("""SELECT * FROM tblnewprojects""")
    row = FetchOneAssoc(c)
    while row is not None:
        if row['name'] is not None:
            projectstatus = m.projectstatus.get(
                row.get('fkProjectStatusId'), {'code': 'U', 'description': 'Unknown'})
            p, created = Project.objects.get_or_create(pk=row.get('pkProjectId'))
            p.name = _d(row.get('name'))
            p.enddate = row.get('endDate')
            p.startdate = row.get('startDate')
            p.description = _d(row.get('description'))
            p.status = ProjectStatus.objects.get_or_create(**projectstatus)[0]
            p.verified = row.get('verified')
            p.save()

            try:
                ProjectOrganization.objects.get_or_create(
                    organization=Organization.objects.get(pk=row.get('fkOrganizationId')),
                    project=p,
                    organizationclass_id='P')
            except Organization.DoesNotExist:
                pass

        row = FetchOneAssoc(c)


def importprojectpartners():

    c.execute(property_queries['projectpartners'])

    for pid, oid in c.fetchall():
        try:
            po, created = ProjectOrganization.objects.get_or_create(
                organization_id=oid, project_id=pid, organizationclass_id='A'
            )
            po.save()
        except Exception, e:
            logging.warn(e)


def projectproperties():
    c.execute(property_queries['ben'])

    for pid, benid in c.fetchall():
        try:

            d = m.ben.get(benid)
            if not d:
                logging.warn('Specified {} pk={} which does not exist'.format('beneficiary', benid))
                continue
            tag = PropertyTag.objects.get(path=d['path'])
            Project.objects.get(pk=pid).beneficiary.add(tag)

        except Exception, e:
            logging.warn(e)
            logging.warn('Project id {}, Beneficary ID {}'.format(pid,benid))

    c.execute(property_queries['act'])

    for pid, actid in c.fetchall():
        try:
            d = m.act.get(actid)
            if not d:
                logging.warn('Specified {} pk={} which does not exist'.format('activity', actid))
                continue
            tag = PropertyTag.objects.get(path=d['path'])
            Project.objects.get(pk=pid).activity.add(tag)
        except Exception, e:
            logging.warn(e)
            logging.warn('Project id {}, Activity ID {}'.format(pid,actid))

    c.execute(property_queries['inv'])

    for pid, invid in c.fetchall():
        try:
            d = m.inv.get(invid)
            if not d:
                logging.warn('Specified {} pk={} which does not exist'.format('involvement', invid))
                continue
            tag = PropertyTag.objects.get(path=d['path'])
            Project.objects.get(pk=pid).sector.add(tag)
        except Exception, e:
            logging.warn(e)
            logging.warn('Project id {}, Inv ID {}'.format(pid,invid))

def projectpersons():
    ProjectPerson.objects.all().delete()

    c.execute(
        '''SELECT pkProjectId, fkPrimaryContactId, true FROM tblnewprojects WHERE fkPrimaryContactId IN (SELECT pkPersonId FROM tblpeople) AND fkPrimaryContactId IS NOT NULL
           UNION
           SELECT pkProjectId, fkSecondaryContactId, false FROM tblnewprojects WHERE fkSecondaryContactId IN (SELECT pkPersonId FROM tblpeople) AND fkSecondaryContactId IS NOT NULL
           UNION
           SELECT fKProjectId, fKPersonId, false FROM tblprojectstaff WHERE fKPersonId IN (SELECT pkPersonId FROM tblpeople) AND fKProjectId IN (SELECT pkProjectId FROM tblnewprojects) AND fKProjectId IS NOT NULL AND fKPersonId IS NOT NULL
          ''')
    person_ids = []
    for project_id, person_id, primary in c.fetchall():
        if person_id in person_ids:
            continue
        try:
            ProjectPerson.objects.get_or_create(project_id=project_id, person_id=person_id, is_primary=primary)
            person_ids.append(person_id)
        except Exception, e:
            logging.warn(e)
            continue



def coalesce(test_values, valid_values):
    """
    Returns the first matched item of two lists

    Args:
        codes (list): The list to process
    Returns:
        The first non-null value
    """
    for i in test_values:
        if i in valid_values:
            return valid_values[i]
    return None


def projectaddresses():
    c.execute(
        'select fkProjectId, fkDistrictCode, fkSubDistrictCode, fkSucosCode, discription FROM tblprojaddresses WHERE fkProjectId IN (SELECT pkProjectId FROM tblnewprojects)')

    for pid, districtcode, subdcode, sucocode, desc in c.fetchall():
        try:
            project = Project.objects.get(pk=pid)
        except Project.DoesNotExist:
            logging.warn('Unexpected Project does not exist')
            continue
        try:
            placeObject = Place.objects.get(pk=coalesce((sucocode, subdcode, districtcode), m.pcodes))
        except Place.DoesNotExist:

            if sucocode == 999999:
                continue

            else:
                logging.warn('Place ({} / {} / {}) does not exist'.format(sucocode, subdcode, districtcode))
            continue

        ProjectPlace.objects.get_or_create(project=project, place=placeObject)


def organizationplace():
    OrganizationPlace.objects.all().delete()
    c.execute('''
    SELECT fkOrganizationId, fkSucosCode, fkSubDistrictCode,fkDistrictCode, discription, primaryPhone, email FROM tblorgaddresses, tblneworganizations WHERE fkOrganizationId = pkOrganizationId
    AND fkOrganizationId IN (SELECT pkOrganizationId from tblneworganizations)
    '''
    )

    for oid, pcodea, pcodeb, pcodec, desc, phone, email in c.fetchall():
        place_id=coalesce((pcodea, pcodeb, pcodec), m.pcodes)
        try:
            point = AdminArea.objects.get(pk = place_id).geom.centroid
        except AdminArea.DoesNotExist, e:
            point = GEOSGeometry('POINT(125.653 8.405)'),
            logging.warn('{} {} {}'.format(e, oid, 'This organization needs its location updated'))
            continue

        try:
            organization = Organization.objects.get(pk = oid)
        except Organization.DoesNotExist, e:
            logging.warn('{} {} {}'.format(e, oid, 'This organization is not in the new database'))
            continue

        try:
            OrganizationPlace(
                organization = organization,
                description = _d(desc),
                point = point,
                phone = phone,
                email = email
            ).save()

        except Exception, e:
            logging.warn('{} {} {}'.format(e, oid, desc))


if __name__ == "__main__":
    # pass
    setup()
    logging.info('Starting organization import')
    importorganizations()
    logging.info('Starting project import')
    importprojects()
    importprojectpartners()
    logging.info('Starting projectproperties()')
    projectproperties()
    logging.info('Starting persons()')
    importpersons()
    logging.info('Starting addresses()')
    projectaddresses()
    logging.info('Starting projpersons()')
    projectpersons()
    logging.info('Starting places()')
    organizationplace()
