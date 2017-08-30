import json

from django.template.loader import get_template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django_tables2 import Table, Column
import django_tables2 as tables
from suggest.models import Suggest

__author__ = 'josh'


class SuggestTable(Table):
    email_obfs = Column()
    id = Column()
    url = Column()
    data = Column()

    class Meta:
        model = Suggest
        attrs = {"class": "paleblu"}
        fields = (
            'description', 'data', 'user_name', 'suggestDate', 'approvalDate', 'email_obfs', 'url', 'children', 'parent')

    def render_data(self, value, record):
        novalues = []
        r = '<table>'
        for k, v in list(record.changes.items()):
            if v:
                r += "\n\t<tr><td>{}</td><td>{}</td></tr>".format(k, v)
            else:
                novalues.append(k)
        r += '\n</table>'
        if novalues:
            r += 'No data for: {}'.format(', '.join(novalues))

        return mark_safe(r)

    def render_description(self, value, record):
        # change_url = urlresolvers.reverse('admin:nhdb_project_change', args=[A('pk')])
        # detail_url = urlresolvers.reverse('nhdb:project:detail', kwargs={'pk': record.pk})

        detail_url = '#object=' + str(record.pk)
        returns = '<a href="{}">{}</a>'.format(detail_url, value)
        #
        # for i in record.children():
        #     if i.prepare['ready']:
        #         returns += u'<br><a href="#object={}">&nbsp;{}</a>'.format(i.pk, i)
        #     else:
        #         returns += u'<br><a href="#object={}"><span style="color:red">&nbsp;{}</span></a>'.format(i.pk, i)

        return mark_safe(returns)

    def render_children(self, value):

        pattern = '<a href="#object={i.pk}">{i}</a>'
        return mark_safe(''.join([pattern.format(i=link) for link in value.all()]))
        #
        # r = ''
        # for i in value:
        #     detail_url = '#object=' + str(i.pk)
        #     r += u'<p><a href="{}">{}</a></p>'.format(detail_url, i)
        # return mark_safe(r)

    def render_parent(self, value):

        pattern = '<a href="#object={i.pk}">{i}</a>'
        return mark_safe(''.join([pattern.format(i=link) for link in value.all()]))

        r = ''
        for i in value:
            detail_url = '#object=' + str(i.pk)
            r += '<p><a href="{}">{}</a></p>'.format(detail_url, i)
        return mark_safe(r)

    def render_url(self, value, record):
        p = record.prepare
        cancelform = get_template('suggest/forms/cancel.html').render({'record': record})
        if not p['ready']:
            f = "<p> Can't apply changes yet.<br> {} </p>".format(p['exception'])
            notreadyform = get_template('suggest/forms/not_ready.html').render({'record': record})
            return mark_safe(notreadyform + cancelform)

        if record.state == 'W':
            if record.method == 'DELETE':
                form = get_template('suggest/forms/delete.html').render({'record': record})
            else:
                form = get_template('suggest/forms/main.html').render({'record': record})
            return mark_safe(form + cancelform)

        elif record.state == 'A':
            return mark_safe('<span style="color:{}">{}</span>'.format('green', record.get_state_display()))
        elif record.state == 'R':
            return mark_safe('<span style="color:{}">{}</span>'.format('red', record.get_state_display()))
        elif record.state == 'X':
            return mark_safe('<span style="color:{}">{}</span>'.format('red', record.get_state_display()))
        elif record.state == 'D':
            return mark_safe('<span style="color:{}">{}</span>'.format('gray', record.get_state_display()))

        return mark_safe('<p>{}</p>'.format(record.get_state_display()))
