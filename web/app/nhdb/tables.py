from django.core import urlresolvers
from django.utils.safestring import mark_safe
from django_tables2 import LinkColumn, Column, Table
from nhdb.models import Organization, Project, PropertyTag, ProjectPerson, Email, Person
from django_tables2.utils import A

__author__ = 'josh'


class ProjectPersonTable(Table):
    class Meta:
        model = ProjectPerson
        attrs = {"class": "paleblu"}
        exclude = ('project',)


class PersonTable(Table):
    class Meta:
        model = Person
        attrs = {"class": "paleblu"}
        exclude = ('title',)

    def render_email(self, value, record):
        return Email(record.email).rot

    def render_name(self, value, record):

        detail_url = '#object='+str(record.pk)
        return mark_safe(u'<a href="{}">{}</a><br><span class="table-person-name">{}</span>'.format(detail_url, value,  record.title or ''))


class PersonProjectTable(Table):
    class Meta:
        model = ProjectPerson
        attrs = {"class": "paleblu"}
        exclude = ('person',)


class OrganizationTable(Table):
    class Meta:
        model = Organization
        exclude = ('pk','fongtilid', 'justiceid', 'name_en', 'name_tet', 'name_pt', 'name_id',
        'description', 'description_en', 'description_tet', 'description_pt', 'description_id',
        'stafffulltime', 'staffparttime')

        attrs = {"class": "paleblu"}

    organization_phone = Column(accessor='contact.phoneprimary')
    email = Column()

    def render_email(self, value, record):
        return Email(record.email).rot

    def render_name(self, value, record):
        change_url = urlresolvers.reverse('admin:nhdb_project_change', args=[A('pk')])
        # detail_url = urlresolvers.reverse('nhdb:project:detail', kwargs={'pk': record.pk})
        detail_url = '#object='+str(record.pk)
        return mark_safe(u'<a href="{}">{}</a><br><span class="table-organization-description">{}</span>'.format(detail_url, value,  record.description or ''))


class ProjectTable(Table):
    class Meta:
        model = Project
        attrs = {"class": "paleblu"}
        fields = ('name', 'startdate', 'enddate', 'verified', 'status')

    sector = Column()
    organization = Column()

    def render_sector(self, value):
        return ', '.join([activity.name for activity in value.all()])

    def render_organization(self, value, record):

        returns = []
        for name, pk, org_class in record.projectorganization_set.values_list('organization__name', 'organization__pk', 'organizationclass__description'):
            detail_url = "/nhdb/organization/?q=active.true#object=%s"%(pk)
            returns.append(u'<a href="{}">{}({})</a><br>'.format(detail_url, name, org_class))
        return mark_safe('\n'.join(returns))

    def render_name(self, value, record):
        change_url = urlresolvers.reverse('admin:nhdb_project_change', args=[A('pk')])
        # detail_url = urlresolvers.reverse('nhdb:project:detail', kwargs={'pk': record.pk})
        detail_url = '#object='+str(record.pk)
        return mark_safe(u'<a href="{}">{}</a><br><span class="table-project-description">{}</span>'.format(detail_url, value,  record.description or ''))


class PropertyTagTable(Table):
    class Meta:
        model = PropertyTag
        attrs = {"class": "paleblu"}

    id = LinkColumn('nhdb:propertytag:update', args=[A('pk')])