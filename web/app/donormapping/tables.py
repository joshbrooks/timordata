from django.utils.safestring import mark_safe
import django_tables2 as tables
from donormapping.models import FundingOffer, FundingSurvey, DonorSurveyResponse
from django_tables2.utils import A
from django_tables2 import LinkColumn, Column, Table


class FundingSurveyTable(tables.Table):
    class Meta:
        model = FundingSurvey
        attrs = {"class": "paleblu"}


class DonorSurveyResponseTable(tables.Table):
    class Meta:
        model = DonorSurveyResponse
        attrs = {"class": "paleblu"}


class FundingOfferTable(tables.Table):
    activity = tables.Column()
    sector = tables.Column()
    beneficiary = tables.Column()
    # test = tables.Column()
    title = LinkColumn('donormapping:fundingoffer:detail', args=[A('pk')])

    def render_activity(self, value):
        return ', '.join([activity.name for activity in value.all()])

    def render_sector(self, value):
        return ', '.join([activity.name for activity in value.all()])

    def render_beneficiary(self, value):
        return ', '.join([activity.name for activity in value.all()])

    def render_title(self, value, record):
        detail_url = '#object='+str(record.pk)
        return mark_safe('<a href="{}">{}</a><br><span class="table-organization-description"><em>{}</em></span>'.format(
            detail_url, value, record.organization.name))

    class Meta:
        model = FundingOffer
        fields = ('title', 'activity')
        attrs = {"class": "paleblu"}