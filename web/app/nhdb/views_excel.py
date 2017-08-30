from datetime import date
from django.utils.translation import ugettext as _
from export.excel_export import ExportTemplateWriter
from .views import get_organization_queryset, get_projects_page
import logging

logger = logging.getLogger(__name__)


def project(request, object_list=None):
    if object_list is None:
        object_list = get_projects_page(request)
    logger.debug(object_list)
    object_list = object_list.prefetch_related('projectorganization_set', 'organization')

    row = 1
    columns = (
        (0, _('Name'), 50),
        (1, _('Description'), 50),
        (2, _('Start Date'), 23),
        (3, _('End Date'), 23),
        (4, _('Organizations'), 50),
        (5, _('Partners'), 50),
        (6, _('Funding'), 50),
        (7, _('Other Organizations'), 50)
    )

    workbook = ExportTemplateWriter(columns=columns, header_row=row)
    sheet = workbook.worksheet

    for obj in object_list:
        row += 1
        text_format = workbook.workbook.add_format({'text_wrap': True})
        sheet.write(row, 0, obj.name, text_format)
        sheet.write(row, 1, obj.description)
        if obj.startdate:
            sheet.write(row, 2, obj.startdate, workbook.date_format)
        if obj.enddate:
            sheet.write(row, 3, obj.enddate, workbook.date_format)

        organizations_primary = ', '.join([i.organization.name for i in obj.projectorganization_set.filter(
            organization_id__isnull=False, organizationclass='P')])
        sheet.write(row, 4, organizations_primary)

        organizations_partner = ', '.join([i.organization.name for i in obj.projectorganization_set.filter(
            organization_id__isnull=False, organizationclass='A')])
        sheet.write(row, 5, organizations_partner)

        organizations_funding = ', '.join([i.organization.name for i in obj.projectorganization_set.filter(
            organization_id__isnull=False, organizationclass='F')])
        sheet.write(row, 6, organizations_funding)

        organizations_other = ', '.join([i.organization.name for i in obj.projectorganization_set.filter(
            organization_id__isnull=False, organizationclass='O')])
        sheet.write(row, 7, organizations_other)

        sheet.set_row(row, 15 * len(obj.organization.all()))

    return workbook.response(filename='nhdb-projects-{}.xlsx'.format(date.today().isoformat()))


def organization(request, object_list=None):
    if not object_list:
        object_list = get_organization_queryset(request)
    object_list = object_list\
        .prefetch_related('organizationplace_set__organizationplacedescription')\
        .prefetch_related('orgtype')\
        .prefetch_related('primary_contact_person')

    row = 1
    columns = (
        (0, _('Name'), 50),
        (1, _('Type'), 50),
        (2, _('Phone'), 50),
        (3, _('Email'), 23),
        (4, _('Primary Contact'), 20),
        (5, _('Addresses'), 23),
        (6, _('District'), 20),
        (7, _('Subdistrict'), 20),
        (8, _('Suco'), 20)
    )

    workbook = ExportTemplateWriter(columns=columns, header_row=row)
    sheet = workbook.worksheet

    for object in object_list:
        row += 1

        phone = object.phoneprimary or ''
        if object.phonesecondary:
            phone += '\n' + object.phonesecondary

        address_rows = max(object.organizationplace_set.count(), 1)
        if address_rows > 1:
            sheet.merge_range(row, 0, row + address_rows - 1, 0, object.name)
        else:
            sheet.write(row, 0, object.name)
        sheet.write(row, 2, phone)
        sheet.write(row, 1, object.orgtype.orgtype)
        sheet.write(row, 3, object.email)

        if object.primary_contact_person:
            sheet.write(row, 4, '{}'.format(object.primary_contact_person.first() or ''))

        address_row = 0
        for organizationplace in object.organizationplace_set.all():
            sheet.write(row + address_row, 5, organizationplace.description)
            try:
                sheet.write(row + address_row, 6, organizationplace.organizationplacedescription.suco)
                sheet.write(row + address_row, 7, organizationplace.organizationplacedescription.subdistrict)
                sheet.write(row + address_row, 8, organizationplace.organizationplacedescription.district)
            except:
                pass
            address_row += 1

    return workbook.response(filename='nhdb-organizations-{}.xlsx'.format(date.today().isoformat()))
