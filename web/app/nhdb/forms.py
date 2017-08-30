from datetime import datetime
from belun import settings
from belun.settings import LANGUAGES_FIX_ID
from crispy_forms.bootstrap import TabHolder, PrependedText, FormActions, AccordionGroup, Accordion
from django.apps import apps
from django.utils.safestring import mark_safe
from nhdb.models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Field, Div, Fieldset, Hidden
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as u_
from suggest.forms import SuggestionForm
from suggest.models import Suggest


def getchoices(model, field='pk', field_display=None):
    try:
        return [(getattr(i, field), getattr(i, field_display)) for i in model.objects.all()]
    except:
        # raise a warning
        return []


def radiobuttons(inputs):
    '''
    Frequent errors result from using checkboxes to represent boolean values ('ON' is not valid for REST api)
    Returns radio buttons. Each button needs parameter name, value, is_default, label
    :param input:
    :return:
    '''

    # Tuple : [name, value, "checked" or None, label]
    radios = []
    for i in inputs:
        radios.append('''
            <div class="radio">
              <label>
                <input type="radio" name="{}" value="{}" {}>
                  {}
                </label>
              </div>'''.format(i))

    return HTML(''.join(radios))


class ExcelDownloadForm(forms.ModelForm):
    class Meta:
        model = ExcelDownloadFeedback
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(ExcelDownloadForm, self).__init__(*args, **kwargs)

    @property
    def helper(self):
        helper = FormHelper()
        helper.attrs = {'action': '/nhdb/downloadexcel/'}
        helper.form_id = "excel-download-form"
        helper.form_class = 'form-horizontal'
        helper.label_class = 'col-lg-3'
        helper.field_class = 'col-lg-9'

        return helper


class OrganizationForm(SuggestionForm):
    class Meta:
        model = Organization
        exclude = ('description', 'description_en', 'description_tet', 'description_pt', 'description_ind')
        fields = ('name', 'orgtype', 'stafffulltime', 'staffparttime')  # , 'active')

    def __init__(self, organization=None, *args, **kwargs):
        super(OrganizationForm, self).__init__(_instance=organization, *args, **kwargs)
        self.organization = organization

    @property
    def helper(self):
        helper = self.get_helper()

        # TODO: Make "active" or "Inactive" selected
        # Note that we're overriding the "active" because form submission will simply drop an unticked checkbox
        # which makes things difficult for the Suggest API
        helper.layout.extend([
            Fieldset('Required Fields',
                     'name',
                     'orgtype',
                     HTML("""
                        <label class="radio-inline">
                          <input type="radio" name="active" id="inlineRadio1" value="on"> Active
                        </label>
                        <label class="radio-inline">
                          <input type="radio" name="active" id="inlineRadio2" value="off"> Inactive
                        </label>"""),
                     ),
            Fieldset('Size',
                     'stafffulltime',
                     'staffparttime')])

        return helper


class OrganizationDescriptionForm(SuggestionForm):
    description = forms.CharField()
    description_en = forms.CharField()
    description_tet = forms.CharField()
    description_ind = forms.CharField()
    description_pt = forms.CharField()

    class Meta:
        model = Organization
        fields = []

    def __init__(self, language='en', suggest=None, organization=None, *args, **kwargs):

        if hasattr(self.Meta, 'instance_name'):
            _instance = locals().get(getattr(self.Meta, 'instance_name'))
        else:
            _instance = locals().get(self.Meta.model._meta.model_name)
        self.suggest, self.organization, self._language = suggest, organization, language
        super(OrganizationDescriptionForm, self).__init__(_instance, *args, **kwargs)

    @property
    def helper(self):

        helper = self.get_helper()
        current_text = getattr(self.organization, 'description_' + self._language)

        helper.layout.extend([
            HTML('<p><b>Currently:</b> %s</p>' % (current_text)),
            Field('description_{}'.format(self._language)),
        ])

        return helper


class ExcelDownloadFeedbackForm(forms.ModelForm):
    class Meta:
        model = ExcelDownloadFeedback
        exclude = ()

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal'
        helper.form_id = self.Meta.model._meta.model_name + '-form'
        helper.label_class = 'col-lg-3'
        helper.field_class = 'col-lg-9'
        return helper


class ProjectdescriptionForm(SuggestionForm):
    description = forms.CharField()
    description_en = forms.CharField()
    description_tet = forms.CharField()
    description_ind = forms.CharField()
    description_pt = forms.CharField()

    class Meta:
        model = Project
        fields = []

    def __init__(self, project=None, suggest=None, language='en', *args, **kwargs):

        if hasattr(self.Meta, 'instance_name'):
            _instance = locals().get(getattr(self.Meta, 'instance_name'))
        else:
            _instance = locals().get(self.Meta.model._meta.model_name)

        self.language = language

        super(ProjectdescriptionForm, self).__init__(_instance, *args, **kwargs)

    @property
    def helper(self):
        helper = self.get_helper()
        helper.layout.append(Field('description_%s' % (self.language)))
        return helper


def get_adminarea_list():
    def indent(i):
        if i.pk < 100:
            return ''
        if i.pk > 100 and i.pk < 10000:
            return '&nbsp;' * 2
        return '&nbsp;' * 4

    placechoices = []
    try:
        for place in apps.get_model('geo', 'adminarea').objects.order_by('path').values_list('pk', 'name'):
            placechoices.append((place[0], mark_safe('{}{}'.format(indent(place[1]), place[1]))))
    except:
        pass
    return placechoices


class OrganizationSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(OrganizationSearchForm, self).__init__(*args, **kwargs)
        self.fields['act'].choices = [(p.path, _(p.name)) for p in PropertyTag.objects.filter(path__startswith="ACT.")]
        self.fields['ben'].choices = [(p.path, _(p.name)) for p in PropertyTag.objects.filter(path__startswith="BEN.")]
        self.fields['inv'].choices = [(p.path, _(p.name)) for p in PropertyTag.objects.filter(path__startswith="INV.")]
        self.fields['orgtype'].choices = [(i.pk, i.orgtype) for i in OrganizationClass.objects.all()]
        self.fields['pcode'].choices = get_adminarea_list(),

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal datacenter-search-form'
        helper.label_class = 'col-lg-2'
        # .helper.field_template = 'bootstrap3/layout/inline_field.html'
        helper.field_class = 'col-lg-10'
        helper.form_method = 'get'

        helper.layout = Layout(

            Div(Fieldset(_('Search Organizations'),
                         HTML('''<div class="btn-group"  data-toggle="button">
                              <a class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="collapse" href="#div_id_act">
                                Activities
                              </a>
                              <a class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="collapse" href="#div_id_ben">
                                Beneficiaries
                              </a>
                              <a class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="collapse" href="#div_id_inv">
                                Sectors
                              </a>
                             <a class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="collapse" href="#div_id_pcode">
                                Place
                              </a>
                                <a class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="collapse" href="#div_id_orgtype">
                                Organization type
                              </a>
                                <a class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="collapse" href="#div_id_name">
                                Organization name
                              </a>
                            </div>'''),
                         Field('name', wrapper_class="collapse"),
                         Field('act', data_selecttwo='true', css_class='select2_auto', wrapper_class="collapse"),
                         Field('inv', data_selecttwo='true', css_class='select2_auto', wrapper_class="collapse"),
                         Field('ben', data_selecttwo='true', css_class='select2_auto', wrapper_class="collapse"),

                         Field('orgtype', wrapper_class="collapse"),
                         Field('pcode', wrapper_class="collapse"),
                         # Field('inactive'),
                         ),
                Submit('search', u_('Search'), css_class="btn btn-success btn"),
                )
        )

        return helper

    act = forms.MultipleChoiceField(label=_('Activity'), required=False)
    inv = forms.MultipleChoiceField(label=_('Sector'), required=False)
    ben = forms.MultipleChoiceField(label=_('Beneficiary'), required=False)
    orgtype = forms.MultipleChoiceField(label=_('Organization Type'), required=False)

    name = forms.CharField(
        required=False,
        label='Name')

    pcode = forms.MultipleChoiceField(
        required=False,
        label=_("Place"),

        help_text="Limit the search to active organizations in these places",
    )


class ProjectpropertiesForm(SuggestionForm):
    class Meta:
        model = Project
        fields = ("activity", "beneficiary", "sector", 'notes')

    def __init__(self, project=None, language='en', *args, **kwargs):

        if hasattr(self.Meta, 'instance_name'):
            _instance = locals().get(getattr(self.Meta, 'instance_name'))
        else:
            _instance = locals().get(self.Meta.model._meta.model_name)

        super(ProjectpropertiesForm, self).__init__(_instance, *args, **kwargs)
        self._instance = _instance

    @property
    def helper(self):
        if isinstance(self._instance, Project):
            helper = self.get_helper(url='/rest/nhdb/projectpropertiesbyid/{}/'.format(self._instance.pk))
        elif isinstance(self._instance, Suggest):
            helper = self.get_helper(url='/rest/nhdb/projectpropertiesbyid/_{}/'.format(self._instance.pk))

        helper.form_id = 'update-projectproperties-form'

        helper.layout.extend([
            Field('activity', data_selecttwo='true', css_class='select2_auto', style='width:90%'),
            Field('sector', data_selecttwo='true', css_class='select2_auto', style='width:90%'),
            Field('beneficiary', data_selecttwo='true', css_class='select2_auto', style='width:90%'),
            Field('notes'),
            #  Hidden fields indicate to treat this as a list, not as a value
            Hidden('has_many', 'activity'),
            Hidden('has_many', 'sector'),
            Hidden('has_many', 'beneficiary'),
            FormActions(
                Submit('__action', 'Update'),
            )
        ])

        return helper


class ProjectTranslationsForm(SuggestionForm):
    class Meta:
        model = Project
        exclude = []

    def __init__(self, project=None, language='en', *args, **kwargs):

        if hasattr(self.Meta, 'instance_name'):
            _instance = locals().get(getattr(self.Meta, 'instance_name'))
        else:
            _instance = locals().get(self.Meta.model._meta.model_name)

        super(ProjectTranslationsForm, self).__init__(_instance, *args, **kwargs)

    @property
    def helper(self):
        helper = self.get_helper()
        a = [AccordionGroup(n, "name_" + c, "description_" + c) for c, n in LANGUAGES_FIX_ID]
        helper.layout.append(Accordion(*a))
        return helper


class ProjectOtherPropertiesForm(SuggestionForm):
    '''
    Catch any fields which do not fall into the other suggestion forms
    '''

    class Meta:
        model = Project
        fields = ('startdate', 'enddate', 'status', 'projecttype', 'staffparttime', 'stafffulltime')
        instance_name = 'project'

    def __init__(self, project, *args, **kwargs):
        if hasattr(self.Meta, 'instance_name'):
            _instance = locals().get(getattr(self.Meta, 'instance_name'))
        else:
            _instance = locals().get(self.Meta.model._meta.model_name)
        self.project = project
        super(ProjectOtherPropertiesForm, self).__init__(_instance=_instance, *args, **kwargs)

    @property
    def helper(self):
        helper = self.get_helper()
        helper.layout.extend(['startdate', 'enddate', 'status', 'projecttype', 'staffparttime', 'stafffulltime'])
        return helper


project_form_fields = ['status',
                       'projecttype',
                       'startdate',
                       'enddate',
                       'stafffulltime',
                       'staffparttime',
                       ]


# for code, name in settings.LANGUAGES:
#     for fieldname in ['name', 'description']:
#         project_form_fields.append('{}_{}'.format(fieldname, code))

def translation_accordion(field_list=(), instance=None):
    accordion_groups = []

    for language_code, lanuage_name in LANGUAGES_FIX_ID:
        fields = []
        for field_name in field_list:
            field_name_trans = '{}_{}'.format(field_name, language_code)
            if instance:
                fields.append(Field(field_name_trans, value=getattr(instance, field_name_trans, '') or ''))
            else:
                fields.append(field_name_trans)
        accordion_groups.append(AccordionGroup(lanuage_name, *fields))
    return Accordion(*accordion_groups)


class ProjectForm(SuggestionForm):
    name_en = forms.CharField()
    name_pt = forms.CharField()
    name_ind = forms.CharField()
    name_tet = forms.CharField()
    description_tet = forms.CharField()
    description_pt = forms.CharField()
    description_en = forms.CharField()
    description_ind = forms.CharField()

    class Meta:
        model = Project
        # fields = project_form_fields
        fields = project_form_fields

    def __init__(self, project=None, suggest=None, organization=None, *args, **kwargs):

        if hasattr(self.Meta, 'instance_name'):
            _instance = locals().get(getattr(self.Meta, 'instance_name'))
        else:
            _instance = locals().get(self.Meta.model._meta.model_name)

        self.project, self.suggest, self.organization = project, suggest, organization
        super(ProjectForm, self).__init__(_instance=_instance, *args, **kwargs)

    @property
    def helper(self):

        helper = self.get_helper()

        languages = settings.LANGUAGES_FIX_ID
        msg = _("You can add translations in these languages: ")
        msg += ', '.join([i[1] for i in languages])

        helper.layout.append(translation_accordion(field_list=['name', 'description'], instance=self.project))

        helper.layout.extend([
            'status',
            'projecttype',
            Field('startdate', css_class="apply_datepicker"),
            Field('enddate', css_class="apply_datepicker"),
            Field('stafffulltime', css_class='col-lg-4'),
            Field('staffparttime', css_class='col-lg-4'),
        ])
        return helper


class ProjectImageForm(SuggestionForm):
    class Meta:
        model = ProjectImage
        fields = ('description', 'image', 'project')

    def __init__(self, project=None, projectimage=None, *args, **kwargs):
        super(ProjectImageForm, self).__init__(projectimage, *args, **kwargs)
        self.project = project
        self.set_field_opts(name='project', instance=projectimage)

    @property
    def helper(self):
        helper = self.get_helper()
        helper.form_tag = True  # So that we can change enctype (allow file uploads)
        helper.attrs['enctype'] = "multipart/form-data"
        helper.form_class = 'form-horizontal'
        helper.form_id = 'project-image-form'
        helper.label_class = 'col-lg-3'
        helper.field_class = 'col-lg-9'

        helper.layout.extend([
            'description',
            'image',
            Field('project', data_selecturl='/selecttwo/nhdb/project/name/icontains',
                  wrapper_class=self.get_wrapper_class('project'))
        ])

        return helper


class BaseSuggestionForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(), label="Your name")
    email = forms.EmailField(widget=forms.EmailInput(), label='your_email@gmail.com')
    comment = forms.CharField(widget=forms.TextInput(), label="Comment on your changes", required=False)

    def __init__(self, *args, **kwargs):
        super(BaseSuggestionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline suggestionform-base'

        self.helper.layout = Layout(
            'name',
            'email',
            'comment',
        )
        self.helper.field_template = 'bootstrap3/layout/inline_field.html'


class ProjectorganizationForm(SuggestionForm):
    class Meta:
        model = ProjectOrganization
        # fields = ['project', 'organization', 'organizationclass']
        fields = ['project', 'organization', 'organizationclass']
        instance_name = 'projectorganization'

    def __init__(self, projectorganization=None, project=None, organization=None, *args, **kwargs):

        super(ProjectorganizationForm, self).__init__(projectorganization, *args, **kwargs)

        self.projectorganization = projectorganization
        self.project = project
        self.organization = organization

        if projectorganization and isinstance(projectorganization, Suggest):
            for i, j in list(projectorganization.data_jsonify().items()):
                if i in self.fields:
                    self.fields[i].initial = j

        self.set_field_opts(name=['project', 'organization'], instance=projectorganization)

    @property
    def helper(self):
        create_organization_elements = {
            'data_add_selecturl': '/selecttwo/nhdb/project/name/icontains',
            'data_add_modalurl': '/nhdb/form/organization/main/',
            'data_add_modalselector': '#stack2',
            'data_add_displayfield': 'name'
        }
        helper = self.get_helper()
        helper.layout.extend(Field('organizationclass'))

        if self.project is None:
            helper.layout.append(
                Field('project', data_selecturl='/selecttwo/nhdb/project/name/icontains', placeholder='project',
                      style='width:75%;'))

        if self.organization is None:
            helper.layout.append(Field('organization', data_selecturl='/selecttwo/nhdb/organization/name/icontains',
                                       placeholder='organization', style='width:75%;', **create_organization_elements))

        return helper


class ProjectDetailsForm(SuggestionForm):
    class Meta:
        model = Project
        fields = ('startdate', 'enddate', 'status', 'projecttype')

    def __init__(self, project, *args, **kwargs):
        super(ProjectDetailsForm, self).__init__(project, *args, **kwargs)
        self.instance = project


class ProjectSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ProjectSearchForm, self).__init__(*args, **kwargs)

        self.fields['inv'] = forms.MultipleChoiceField(
            required=False,
            label=_('Sector(s)'),
            choices=[(i.lowerpathstring(), i.name) for i in PropertyTag.objects.filter(path__startswith="INV.")]
        )
        self.fields['ben'] = forms.MultipleChoiceField(
            required=False,
            label=_("Beneficiaries"),
            choices=[(i.lowerpathstring(), i.name) for i in PropertyTag.objects.filter(path__startswith="BEN.")]
        )
        self.fields['act'] = forms.MultipleChoiceField(
            required=False,
            label=_("Activities"),
            choices=[(i.lowerpathstring(), i.name) for i in PropertyTag.objects.filter(path__startswith="ACT.")]
        )

    name = forms.CharField(
        required=False,
        max_length=100,
        label="Search text"
    )
    status = forms.MultipleChoiceField(
        required=False,
        label="Status",
        choices=getchoices(ProjectStatus, 'code', 'description')
    )

    organization = forms.TypedChoiceField(
        required=False
    )

    orgtype = forms.MultipleChoiceField(
        required=False,
        label="Organization types",
        choices=getchoices(OrganizationClass, 'pk', 'orgtype')
        # choices=[(i.pk, i.orgtype) for i in OrganizationClass.objects.all()]
    )

    enddateafter = forms.DateField(
        initial=datetime.strftime(datetime.today(), '%Y-%m-%d'),
        required=False,
        label="Ends after date")

    startdateafter = forms.DateField(
        required=False,
        label="Starts after date")

    nullenddate = forms.BooleanField(required=False, label="Allow empty end date?")
    nullstartdate = forms.BooleanField(required=False, label="Allow empty start date?")

    pcode = forms.MultipleChoiceField(
        required=False,
        label=_("Place"),
        choices=get_adminarea_list(),
        help_text="Limit the search to active organizations in these districts",
    )

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal datacenter-search-form'
        helper.label_class = 'col-lg-4'
        # self.helper.field_template = 'bootstrap3/layout/inline_field.html'
        helper.field_class = 'col-lg-8'
        wc = 'form-group-sm col-lg-6 col-md-6 col-sm-12 row'
        helper.wrapper_class = wc
        helper.form_method = 'get'

        helper.layout = Layout(

            Div(Fieldset(_('Search Projects'),
                         Field('name', wrapper_class=wc),
                         Field('act', css_class="", wrapper_class=wc),
                         Field('inv', css_class="", wrapper_class=wc),
                         Field('ben', css_class="", wrapper_class=wc),
                         Field('inactive', css_class="", wrapper_class=wc),
                         Field('status', css_class="", wrapper_class=wc),
                         Field('orgtype', css_class="applyselectize", wrapper_class=wc),
                         Field('enddateafter', css_class="datepicker", wrapper_class=wc),
                         Field('startdateafter', css_class="datepicker", wrapper_class=wc),
                         Field('pcode', wrapper_class=wc)
                         ),
                Submit('search', u_('Search'), css_class="btn btn-success btn"),
                )
        )

        return helper


class OrganizationcontactForm(SuggestionForm):
    organization = forms.HiddenInput

    class Meta:
        fields = ('phoneprimary', 'phonesecondary', 'email', 'fax', 'web', 'facebook')
        model = Organization

    def __init__(self, organization, suggest=None, language='en', *args, **kwargs):
        super(OrganizationcontactForm, self).__init__(organization, *args, **kwargs)


class OrganizationplaceForm(SuggestionForm):
    class Meta:
        fields = ('description', 'phone', 'email', 'organization')
        model = OrganizationPlace

    def __init__(self, organization=None, organizationplace=None, *args, **kwargs):
        super(OrganizationplaceForm, self).__init__(organizationplace, *args, **kwargs)

        if organizationplace and organizationplace.point:
            self.point_field_value = '{},{}'.format(self.instance.point.x, self.instance.point.y)
        else:
            self.point_field_value = ''

        if organization is None and organizationplace is not None:
            if hasattr(organizationplace, 'organization') and isinstance(organizationplace.organization, Organization):
                organization = organizationplace.organization

        self.organization = organization
        self.instance = organizationplace

        self.set_field_opts(name=['organization'], organization=organization)

    @property
    def helper(self):

        helper = self.get_helper()

        point_field_markup = '''
        <div id="div_id_point" class="form-group"><label for="id_point" class="control-label sr-only">
                point
            </label><div class="controls "><div class="input-group"><span class="input-group-addon"><span class="glyphicon glyphicon-globe" aria-hidden="true"></span></span><input class="textinput textInput form-control" id="id_point" maxlength="256" name="point" placeholder="point" type="text" value="{}"> </div></div></div>
            <div class="leaflet-map" id="leaflet-map" data-point="{}" style="height:200px; width:100%;"></div>
        '''.format(self.point_field_value, self.point_field_value)
        # The "organization_place_map" gives you a place to put in a leaflet based map (or another way to locate place)
        helper.layout.extend([
            HTML(point_field_markup),
            PrependedText('description', '<span class="glyphicon glyphicon-road" aria-hidden="true"></span>',
                          placeholder="description"),
            PrependedText('phone', '<span class="glyphicon glyphicon-phone" aria-hidden="true"></span>',
                          placeholder="phone"),
            PrependedText('email', '<span class="glyphicon glyphicon-envelope" aria-hidden="true"></span>',
                          placeholder="email")
        ])
        helper.add_input('organization')
        return helper


class CollapsibleTranslationFieldset():
    """
    Return a crispyforms "Div(Fieldset(...))" object
    :param title:
    :param ref:
    :return:
    """

    def __init__(self, languages=(('en', 'English')), fields=('name', 'description'),
                 default_fields=('path', 'name', 'description'), wrapper_class='form-group-sm'):
        self.languages = languages
        self.fields = fields
        self.wrapper_class = wrapper_class
        self.default_fields = default_fields

    def toggles(self):
        """
        Return an HTML button for a Layout object which will toggle a fieldset when pressed
        :param title:
        :param ref:
        :return:
        """
        returns = []
        for code, label in self.languages:
            returns.append(HTML(
                '''<a class="btn btn-xs btn-default" data-toggle="collapse" href="#collapsible-{}" aria-expanded="false">{} </a>'''.format(
                    code, label)))
        return returns

    def fieldsets(self, collapsible=True, css_class="row col-md-4"):

        returns = []
        fields = [Field('%s' % (i), wrapper_class=self.wrapper_class) for i in self.default_fields]
        returns.append(Div(Fieldset(_('Default'), *fields), css_class=css_class))
        for language in self.languages:

            if collapsible:
                id = "#collapsible-{}".format(language[1])
                css_class = 'collapse collapsible-%s' % (language[0])

            fields = ([Field('%s_%s' % (i, language[0]), wrapper_class=self.wrapper_class) for i in self.fields])
            returns.append(Div(Fieldset(_(language[1]), *fields), css_class=css_class))
        returns.append(Div(Submit('submit', 'Submit'), css_class="col-lg-12"))
        return returns

    def collapsible(self):

        returns = self.toggles()
        fieldsets = self.fieldsets(collapsible=True)
        returns.extend(fieldsets)

        return returns

    def all(self):
        return self.fieldsets(collapsible=False)


class PropertyTagForm(SuggestionForm):
    class Meta:
        model = PropertyTag
        fields = ('path', 'name', 'description')

    def __init__(self, propertytag=None, *args, **kwargs):
        super(PropertyTagForm, self).__init__(_instance=propertytag, *args, **kwargs)

    @property
    def helper(self):
        helper = self.get_helper()
        helper.form_class = 'form-inline'
        helper.layout.extend(
            Field('path'),
            Accordion(*[AccordionGroup(n, "name_" + c, "description_" + c) for c, n in LANGUAGES_FIX_ID])
        )
        return helper


class ProjectPersonForm(SuggestionForm):
    class Meta:
        exclude = ()
        model = ProjectPerson
        fields = ('is_primary', 'project', 'person')

    def __init__(self, projectperson=None, project=None, person=None, *args, **kwargs):
        _instance = locals().get(self.Meta.model._meta.model_name)
        super(ProjectPersonForm, self).__init__(_instance, *args, **kwargs)
        self.projectperson = projectperson
        self.project = project
        self.person = person
        self.set_field_opts(['person', 'project'])

    @property
    def helper(self):
        create_person_elements = {
            'data_add_selecturl': '/selecttwo/nhdb/person/name/icontains',
            'data_add_modalurl': '/nhdb/form/person/',
            'data_add_modalselector': '#stack2',
            'data_add_displayfield': 'name'
        }

        helper = self.get_helper()
        helper.layout.append(Field('project', data_selecturl='/selecttwo/nhdb/project/name/icontains',
                                   wrapper_class=self.get_wrapper_class('project')))
        helper.layout.append(
            Field('person', data_selecturl='/selecttwo/nhdb/person/name/icontains', **create_person_elements))
        self.fields['person'].choices = []
        return helper


class PersonForm(SuggestionForm):
    '''
    Suggest a new Person. Replaces
    the organization with a dropdown lookup.
    '''

    class Meta:
        exclude = ()
        model = Person

    def __init__(self, person=None, *args, **kwargs):
        # Drop long list of organization names in favor of a select2 box
        super(PersonForm, self).__init__(person, *args, **kwargs)
        if self.instance.organization:
            self.fields['organization'].choices = [(self.instance.organization.pk, self.instance.organization)]
        else:
            self.fields['organization'].choices = []
        self.person = person

    @property
    def helper(self):
        helper = self.get_helper()

        create_organization_elements = {
            'data_add_selecturl': '/selecttwo/nhdb/organization/name/icontains',
            'data_add_modalurl': '/nhdb/form/organization/',
            'data_add_displayfield': 'name'
        }

        helper.layout.extend([
            'name',
            'title',
            Field('organization',
                  data_selecturl='/selecttwo/nhdb/organization/name/icontains',
                  placeholder='organization', **create_organization_elements),
            'phone',
            'email'])

        return helper


class ProjectPlaceForm(SuggestionForm):
    class Meta:
        fields = ('project', 'place')
        model = ProjectPlace

    description = forms.CharField(required=False)

    def __init__(self, projectplace=None, project=None, place=None, *args, **kwargs):
        _instance = locals().get(self.Meta.model._meta.model_name)

        super(ProjectPlaceForm, self).__init__(_instance, *args, **kwargs)
        self.place = place
        self.project = project
        self.set_field_opts(name=['project', 'place'], place=place, project=project)

    @property
    def helper(self):
        helper = self.get_helper()
        helper.form_class = 'form-horizontal'
        helper.layout.append(Field('project', data_selecturl='/selecttwo/nhdb/project/name/icontains',
                                   wrapper_class=self.get_wrapper_class('project')))
        helper.layout.append(Field('place', data_selecturl='/selecttwo/geo/adminarea/name/icontains'))
        helper.layout.append(Field('description'))
        return helper


class ProjectTypeForm(SuggestionForm):
    '''
    Auto generated form class - modify if ncecessary!
    '''

    class Meta:
        model = ProjectType
        exclude = []
        # fields = ()

    def __init__(self, projecttype=None, *args, **kwargs):
        super(ProjectTypeForm, self).__init__(_instance=projecttype, *args, **kwargs)

    @property
    def helper(self):
        helper = self.get_helper()
        helper.layout.extend(['description'])
        helper.layout.extend([])
        return helper

        # ---------------- Auto Generated Forms ---------------
