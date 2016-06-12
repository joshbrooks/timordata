from datetime import date

from export.excel_export import ExportTemplateWriter, FORMATS
from .models import Project, Organization
import logging
logger = logging.getLogger(__name__)
from django.utils.translation import ugettext as _


def project(request, object_list=None):

    if object_list is None:
        object_list = Project.objects.all()
    logger.debug(object_list)
    object_list = object_list.prefetch_related('organization')

    row = 1
    columns = (
        (0, _('Name'), 50),
        (1, _('Description'), 50),
        (2, _('Start Date'), 23),
        (3, _('End Date'), 23),
        (4, _('Organizations'), 50)
    )

    workbook = ExportTemplateWriter(columns = columns, header_row = row)
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

        organizations = '\n'.join([i.name for i in obj.organization.all()])
        sheet.write(row, 4, organizations)
        sheet.set_row(row, 15*len(obj.organization.all()))

    return workbook.response(filename='nhdb-projects-{}.xlsx'.format(date.today().isoformat()))


def organization(request, object_list=None, code='en', refer="timordata.info"):

    if not object_list:
        object_list = Organization.objects.all()
    object_list = object_list.prefetch_related('organizationplace_set__organizationplacedescription').prefetch_related('orgtype')

    row = 1
    column =1
    columns = (
        (0, _('Name'), 50),
        (1, _('Type'), 50),
        (2, _('Phone'), 50),
        (3, _('Email'), 23),
        (4, _('Addresses'), 23),
        (5, _('District'), 20),
        (6, _('Subdistrict'), 20),
        (7, _('Suco'), 20)
    )

    workbook = ExportTemplateWriter(columns = columns, header_row = row)
    sheet = workbook.worksheet

    for object in object_list:
        row += 1

        phone = object.phoneprimary
        if object.phonesecondary:
            phone += '\n' + object.phonesecondary

        address_rows = max(object.organizationplace_set.count(), 1)
        if address_rows > 1:
            sheet.merge_range(row, 0, row+address_rows-1, 0, object.name)
        else:
            sheet.write(row, 0, object.name)
        sheet.write(row, 2, phone)
        sheet.write(row, 1, object.orgtype.orgtype)
        sheet.write(row, 3, object.email)


        address_row = 0
        for organizationplace in object.organizationplace_set.all():
            sheet.write(row + address_row, 4, organizationplace.description)
            sheet.write(row + address_row, 5, organizationplace.organizationplacedescription.suco)
            sheet.write(row + address_row, 6, organizationplace.organizationplacedescription.subdistrict)
            sheet.write(row + address_row, 7, organizationplace.organizationplacedescription.district)
            address_row +=1

    return workbook.response(filename='nhdb-organizations-{}.xlsx'.format(date.today().isoformat()))
