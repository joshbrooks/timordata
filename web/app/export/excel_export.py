import cStringIO as StringIO

import xlsxwriter
from django.http import HttpResponse

FORMATS = {
    'HEADER': {
        'bold': True,
        'size': 25,
        'align': 'center',
        'valign': 'vcenter'
    },
    'DATE': {
        'num_format': 'yyyy-mm-dd',
    },
}


class ExportTemplateWriter(object):

    def __init__(self, columns, header_row = 0,):

        self.output = StringIO.StringIO()
        self.workbook = xlsxwriter.Workbook(self.output)
        self.worksheet = self.workbook.add_worksheet()
        self.worksheet.set_row(0, 30)
        self.date_format = self.workbook.add_format(FORMATS['DATE'])
        self.header_format = self.workbook.add_format(FORMATS['HEADER'])
        self.wrap_format = self.workbook.add_format({'text_wrap': True})

        for col, _string, width in columns:
            self.worksheet.set_column(col, col, width )
            self.worksheet.write_string(header_row, col,_string, self.header_format )

    def response(self, filename='NHDB_projects'):
        self.workbook.close()
        self.output.seek(0)
        response = HttpResponse(self.output.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = "attachment; filename={}.xlsx".format(filename)
        return response
