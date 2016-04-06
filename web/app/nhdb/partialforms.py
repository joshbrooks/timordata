import json
from crispy_forms.bootstrap import InlineField
from django.forms import formset_factory
from django.utils.safestring import mark_safe
from geo.models import AdminArea
from nhdb.models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Div, Button, Field, Fieldset
from django import forms
from django.forms.models import inlineformset_factory
from django_select2.fields import AutoModelSelect2Field, Select2MultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as u_


class PersonSelectField(AutoModelSelect2Field):
    queryset = Person.objects
    search_fields = ['name__icontains', ]


class PlaceSelectField(AutoModelSelect2Field):
    queryset = AdminArea.objects.all().order_by('path')
    search_fields = ['name__icontains', ]

    def __init__(self, *args, **kwargs):
        super(PlaceSelectField, self).__init__(*args, **kwargs)
        self.districts = {}
        for obj in self.queryset.filter(pcode__lt = 100):
            self.districts[obj.pcode] = obj.__unicode__().replace('Distrito De ', '')

    def label_from_instance(self, obj):

        e = obj.geom.envelope.coords
        envelope = json.dumps([(round(i[1],2), round(i[0], 2)) for i in e[0]])

        if obj.pcode < 100:
            value = mark_safe(obj.__unicode__())

        if obj.pcode < 10000:
            d = self.districts.get(obj.pcode // 100)
            value = mark_safe(u'{} - subd. in {}'.format(obj.__unicode__(), d))
        if obj.pcode >= 10000:
            d = self.districts.get(obj.pcode // 10000)
            value = mark_safe(u'{} - suco in {}'.format(obj.__unicode__(), d))

        return "<span data-envelope={}>{}</span>".format(json.dumps(envelope), value)

    def extra_data_from_instance(self, obj):

        e = obj.geom.envelope.coords
        envelope = [(round(i[1],2), round(i[0], 2)) for i in e[0]]
        return {'x':round(obj.geom.centroid.x,2), 'y':round(obj.geom.centroid.y,2),
                'bounds':envelope}


class AddProjectPlaceFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(AddProjectPlaceFormHelper, self).__init__(*args, **kwargs)
        self.layout = Layout(

                InlineField('id'),
                InlineField('place', wrapper_class='col-lg-12'),
                InlineField('description', wrapper_class='col-lg-12'),
                Button('POST', 'Add', css_class='btn-primary btn-xs'),
                HTML('<div class="clearfix"></div>')
        )

        self.form_class = 'form-inline suggestionform-projectplace-add'
        self.field_template = 'bootstrap3/layout/inline_field.html'
        self.form_class = 'suggestionform-projectplace-add'
        self.attrs = {'data_url': '/rest/nhdb/projectplace/'}


class AddProjectPlaceForm(forms.ModelForm):
    class Meta:
        model = ProjectPlace

    def __init__(self, *args, **kwargs):
        super(AddProjectPlaceForm, self).__init__(*args, **kwargs)
        self.helper = AddProjectPlaceFormHelper(self)

    place = PlaceSelectField()


class ChangeProjectPlaceFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(ChangeProjectPlaceFormHelper, self).__init__(*args, **kwargs)
        self.layout = Layout(
                InlineField('id'),
                InlineField('place', wrapper_class='col-lg-12'),
                InlineField('description', wrapper_class='col-lg-12'),
                Button('PUT', 'Change', css_class='btn-primary btn-xs'),
                Button('DELETE', 'Remove', css_class='btn-primary btn-xs'),
                HTML('<div class="clearfix"></div>')
        )

        self.field_template = 'bootstrap3/layout/inline_field.html'
        self.form_class = 'suggestionform-projectplace-change'
        self.attrs = {'data_url': '/rest/nhdb/projectplace/'}


class ChangeProjectPlaceForm(forms.ModelForm):
    class Meta:
        model = ProjectPlace

    def __init__(self, *args, **kwargs):
        super(ChangeProjectPlaceForm, self).__init__(*args, **kwargs)
        self.helper = ChangeProjectPlaceFormHelper(self)
        self.fields['place'].widget.attrs['disabled'] = 'disabled'

    place = PlaceSelectField()


ChangeProjectPlaceFormset = inlineformset_factory(Project, ProjectPlace, form=ChangeProjectPlaceForm, extra=0)
AddProjectPlaceFormset = formset_factory(form=AddProjectPlaceForm, extra=1)


class AddProjectPersonFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(AddProjectPersonFormHelper, self).__init__(*args, **kwargs)
        self.layout = Layout(
            Div(
                Field('person', wrapper_class='col-lg-12'),
                Field('staffclass', wrapper_class='col-lg-6'),
                Div(
                    Submit('submit', 'Add', css_class='btn-primary  btn-xs')
                    , css_class='col-lg-6')
            ), HTML('<div class="clearfix"></div>')
        )
        self.form_class = 'suggestionform-projectperson-add'
        self.label_class = 'sr-only'
        self.wrapper_class = 'col-lg-3 col-md-6 col-sm-12'
        self.attrs = {'data_url': '/rest/nhdb/projectperson/'}


class AddProjectPersonForm(forms.ModelForm):
    class Meta:
        model = ProjectPerson

    def __init__(self, *args, **kwargs):
        super(AddProjectPersonForm, self).__init__(*args, **kwargs)
        self.helper = AddProjectPersonFormHelper(self)

    person = PersonSelectField()


class CreateProjectForm(forms.ModelForm):
    '''
    Show a form to submit a project via the REST.suggest api
    '''
    class Meta:
        model = Project
        fields = ('name', 'description', 'startdate','enddate', 'stafffulltime', 'staffparttime', 'status', 'projecttype')

    #  Allow translated selected fields
    language = forms.ChoiceField(widget=forms.Select, choices=(
        ('tet', 'Tetun',), ('en', 'English',), ('pt', 'Portugese',), ('id', 'Indonesian',)))

    def __init__(self, *args, **kwargs):
        super(CreateProjectForm, self).__init__(*args, **kwargs)
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 5, 'cols': 20})
        self.fields['language'].help_text = "Please enter the language you are writing the <strong>Name</strong> and <strong>Description</strong> with"

    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout(
            Fieldset('Name and Description',
                Field('name', wrapper_class="col-lg-6"),
                Field('projecttype', wrapper_class="col-lg-6"),
                Field('description', wrapper_class="col-lg-6"),
                Field('language', wrapper_class="col-lg-6")
                ),
            Fieldset('Dates / Status',
                 Field('startdate', wrapper_class="col-lg-3"),
                 Field('enddate', wrapper_class="col-lg-3"),
                 Field('status', wrapper_class="col-lg-3"),
                ),

            Fieldset('Staff',
                 Field('stafffulltime', wrapper_class="col-lg-3"),
                 Field('staffparttime', wrapper_class="col-lg-3")
                ),
            Button('status', 'Next'),

            )

        helper.wrapper_class ="col-lg-4 col-sm-6"
        return helper


class CreateProjectFormProperties(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('activity', 'beneficiary', 'sector')

    def __init__(self, *args, **kwargs):
        super(CreateProjectFormProperties, self).__init__(*args, **kwargs)
        help_text="To verify your identity, and in case we need to ask you about your changes"
        self.fields['activity'].help_text = ''
        self.fields['beneficiary'].help_text = ''
        self.fields['sector'].help_text = ''



    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout(
            Fieldset(
                'Properties',
                 Field('activity', css_class='selecttwo'),
                 Field('beneficiary', css_class='selecttwo'),
                 Field('sector', css_class='selecttwo'),
                ),
            Button('status', 'Next')
        )
        return helper

class ChangeProjectPersonFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(ChangeProjectPersonFormHelper, self).__init__(*args, **kwargs)
        self.layout = Layout(

            'id',
            Field('person', wrapper_class='col-lg-12'),
            Field('staffclass', wrapper_class='col-lg-6'),
            Div(
                Button('PUT', 'Change', css_class='btn-primary btn-xs'),
                Button('DELETE', 'Remove', css_class='btn-primary btn-xs')
                , css_class='col-lg-6'
            )
        )

        self.form_class = 'suggestionform-projectperson-change'
        self.label_class = 'sr-only'
        self.wrapper_class = 'col-lg-3 col-md-6 col-sm-12'
        self.attrs = {'data_url': '/rest/nhdb/projectperson/'}


class ChangeProjectPersonForm(forms.ModelForm):
    class Meta:
        model = ProjectPerson

    def __init__(self, *args, **kwargs):
        super(ChangeProjectPersonForm, self).__init__(*args, **kwargs)
        self.helper = ChangeProjectPersonFormHelper(self)
        self.fields['person'].widget.attrs['disabled'] = 'disabled'

    person = PersonSelectField()


ChangeProjectPersonFormset = inlineformset_factory(Project, ProjectPerson, form=ChangeProjectPersonForm, extra=0)
AddProjectPersonFormset = formset_factory(form=AddProjectPersonForm, extra=1)