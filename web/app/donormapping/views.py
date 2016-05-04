import json
import logging
import django
from django.core import serializers
from django.core.urlresolvers import reverse_lazy
from django.db.models import Count
from django.db.models.query_utils import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.template import Context
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.generic import ListView, DetailView
from django_tables2 import SingleTableView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from geo.models import District
from suggest.models import Suggest

from .models import FundingOffer, FundingSurvey, DonorSurveyResponse, FundingOfferDocument
from .forms import FundingSurveyForm, FundingOfferSearchForm, FundingOfferForm, FundingOfferDocumentForm
from nhdb.models import PropertyTag
from pivottable import pivot_table
from .tables import FundingOfferTable, FundingSurveyTable, DonorSurveyResponseTable
from .admin import FundingOfferAdmin
from datetime import datetime

def fundingofferlist(request):

    #
    #
    # class FundingOfferList(SingleTableView):
    #     model = FundingOffer
    #     table_class = FundingOfferTable
    #
    #     def get_context_data(self, **kwargs):
    #         context = super(FundingOfferList, self).get_context_data(**kwargs)

    context = {}
    context['filters'] = {
        'inv': PropertyTag.objects.filter(path__startswith="INV."),
        'act': PropertyTag.objects.filter(path__startswith="ACT."),
        'ben': PropertyTag.objects.filter(path__startswith="BEN."),
        'district': [{'value': 'district.{}'.format(d[1].upper()), 'label': d[0]} for d in
                     District.objects.values_list('name', 'path')],
    }

    context['tabs'] = {
        'first':{'name':'About'},
        'second':{},
        'third':{},
        'fourth':{}
    }

    filter_parameter = 'q'
    context['activefilters'] = request.GET.getlist(filter_parameter)

    get = request.GET
    inv, act, ben, district = Q(), Q(), Q(), Q()

    qs = FundingOffer.objects.all()
    if get.getlist('organization'):
        qs = qs.filter(organization__pk__in =get.getlist('organization') )
    for _f in get.getlist(filter_parameter):

        if _f.lower().startswith('inv.'):
            inv = inv|Q(sector__path=_f.upper())
        elif _f.lower().startswith('act.'):
            act = act|Q(activity__path=_f.upper())
        elif _f.lower().startswith('ben.'):
            ben = ben|Q(beneficiary__path=_f.upper())
        elif _f.lower().startswith('district'):
            district = district|Q(place__path__startswith=_f.split('.')[1].upper())

    qs = qs.filter(inv).filter(ben).\
        filter(act).filter(district).distinct()

    if request.GET.get('expired') != 'True':
        qs = qs.exclude(application_end_date__lt=datetime.today().date())

    qs = qs.prefetch_related('activity','beneficiary','sector','organization')

    context['table'] = FundingOfferTable(qs)


    return render(request, 'donormapping/fundingoffer_list.html', context)

class DonorSurveyResponseView(SingleTableView):
    model = DonorSurveyResponse
    table_class=DonorSurveyResponseTable


class FundingOfferCreate(CreateView):
    model = FundingOffer
    form_class = FundingOfferForm
    # form_class = FundingOfferAdmin


def index(request):
    return render(request, 'donormapping/index.html')


def get_model_choice_counts(field_object, include_zero=True):

    def get_field_choices(field_object):
        """
        Get the Choices available for a model field
        :return:

        """
        fields = django.db.models.fields
        # Raise an error on primary keys - not suitable for summarising

        if isinstance(field_object, django.db.models.fields.AutoField):
            raise TypeError, """Can't call this function on this type of field"""

        elif isinstance(field_object, fields.NullBooleanField):
            choices = ((None, 'No answer'), (True, 'True'), (False, 'False'))

        elif isinstance(field_object, fields.BooleanField):
            choices = ((True, 'True'), (False, 'False'))

        else:
            try:
                choices = field_object.get_choices_default()
            except:
                raise TypeError("Could not get field choices")

        if choices == []:
            raise TypeError("Field has no choices")

        return choices

    labels, data = [], []
    choices = get_field_choices(field_object)
    modelclass = field_object.model

    counts = modelclass.objects.all().values_list(field_object.name).annotate(Count(field_object.name))
    if not counts:
        return [None,None]
    label_codes, values = zip(*counts)  # Creates two separate lists: label and values

    if not choices:
        return

    for code, label in choices:
        try:
            i = label_codes.index(code)
            count = values[i]
        except ValueError:
            # This is a Choice which has not been used yet so its count will be zero
            count = 0

        if count != 0 or include_zero:
            labels.append(label)
            data.append(count)
    return data, labels

class Flot():
    '''
    Return parameters for a flot graph (JSON format)
    :param model:
    :param field:
    :return:
    '''

    def __init__(self, field_object, returntype='auto'):

        self.colors = {
            "True": '#5AED5A',
            "False": '#B8B8B8'}

        self._labels = []
        self._data = []
        self.field_object = field_object
        self.returntype = returntype

    def getcolor(self, value, default='#FFEC86'):

        if value in self.colors:
            return self.colors[value]

        else:
            return None


    @property
    def data(self):
        returntype = self._returntype()

        if returntype == 'categories':
            # Returns a ziplist of label and data
            datasets = zip(self._labels, self._data)

        elif returntype == 'pie':
            # Pie chart wants labels
            datasets = []
            for d in zip(self._labels, self._data):

                label, data = str(d[0]), str(d[1])

                if d[0] in self.colors:
                    datasets.append(
                        {'color': self.getcolor(label), 'label': '{}'.format(label), 'data': '{}'.format(data)})
                else:
                    datasets.append({'label': '{}'.format(label), 'data': '{}'.format(data)})

        else:
            raise TypeError, "Invalid return"
            # Default action
            # data = {'labels':'{}'.format(self._labels),'data':'{}'.format(self._data)}

        return datasets, returntype, self.field_object.verbose_name

    def _returntype(self):
        '''
        When the return type is "Auto" set the return type to be suitable for a pie chart or categories depending on
        the field type
        :return:
        '''
        fields = django.db.models.fields
        field_object = self.field_object
        if self.returntype != 'auto':
            return self.returntype

        fieldtype = type(field_object)
        if fieldtype == fields.IntegerField:
            return 'categories'
        elif fieldtype == fields.CharField:
            return 'categories'
        elif fieldtype == fields.NullBooleanField:
            return 'pie'
        elif fieldtype == fields.BooleanField:
            return 'pie'
        else:
            return 'categories'


class FundingSurveyList(SingleTableView):
    model = FundingSurvey
    table_class = FundingSurveyTable

    def get_context_data(self, **kwargs):
        context = super(FundingSurveyList, self).get_context_data(**kwargs)

        context['test'] = []
        label_lists = []
        data_lists = []
        question_list = []

        field_objects = FundingSurvey._meta.fields
        field_objects.extend([i[0] for i in FundingSurvey._meta.get_m2m_with_model()])
        response = {}

        for field_object in field_objects:

            question_text = _(field_object.verbose_name)

            if field_object.name in ('id', 'organizationname', 'fundinggivemethod', 'fundingrecvmethod'):
                continue
            try:
                data, labels = (get_model_choice_counts(field_object))
            except TypeError, e:
                logging.error("Field type error {}".format(e))
                continue
            if data is None or labels is None:
                continue

            label_lists.append(labels)
            data_lists.append(data)
            question_list.append(question_text)


        for parent in label_lists:
            parent = ','.join(parent)
            if parent not in response.keys():
                response[parent] = []

                for index, child in enumerate(label_lists):
                    child = ','.join(child)
                    if parent == child:
                        qa = [question_list[index]]
                        qa.extend(data_lists[index])
                        response[parent].append(qa)

        for k, v in response.items():
            context['test'].append({'response': k.split(','), 'questions': v})
        # raise AssertionError(context['test'])
        return context


def form(request, model, form):

    args = {}
    f = None
    g = request.GET.get
    p = request.GET.get

    template = 'nhdb/crispy_form.html'

    for m in FundingOffer, FundingOfferDocument:
        m_name = m._meta.model_name

        if g(m_name):
            args[m_name] = m.objects.get(pk = g(m_name))

        # Use an underscore to indicate a suggestion ID
        if g('_'+m_name):
            args[m_name] = Suggest.objects.get(pk = g('_'+m_name))

    # if model in args:
    #     args['instance'] = args[model]

    if model == 'fundingoffer':
        if form == 'main':
            f = FundingOfferForm

    if model == 'fundingofferdocument':
        if form == 'main':
            f = FundingOfferDocumentForm

    if f:
        return render(request, template, {'form': f(**args)})

    return HttpResponseBadRequest(mark_safe("<form>This form '{}' for model '{}' is not available yet</form>".format(form, model)))


class FundingOfferDetail(DetailView):
    model = FundingOffer


class FundingSurveyDetail(DetailView):
    model = FundingSurvey

    def get_context_data(self, **kwargs):
        context = super(FundingSurveyDetail, self).get_context_data(**kwargs)
        context['data'] = serializers.serialize("python", [self.object])

        return context


class FundingSurveyCreate(CreateView):
    model = FundingSurvey
    form_class = FundingSurveyForm


class FundingSurveyEdit(UpdateView):
    model = FundingSurvey
    form_class = FundingSurveyForm


class FundingSurveyDelete(DeleteView):
    model = FundingSurvey
    success_url = reverse_lazy('donormapping:survey:list')