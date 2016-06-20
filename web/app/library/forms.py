
from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Fieldset, Submit, Hidden
from belun.crunchyforms import TranslationTabs
from django.forms import MultipleChoiceField
from library.models import *
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as u_

from nhdb.models import PropertyTag
from suggest.forms import SuggestionForm
from belun.settings import LANGUAGES_FIX_ID


create_author_elements = {
    'data_add_selecturl': '/selecttwo/library/author/name/icontains',
    'data_add_modalurl':  '/library/form/author/main/',
    'data_add_displayfield': 'name'
}
create_organization_elements = {
    'data_add_selecturl': '/selecttwo/nhdb/organization/name/icontains',
    'data_add_modalurl':  '/nhdb/form/organization/main/',
    'data_add_displayfield': 'name'
}
create_pubtype_elements = {
    'data_add_selecturl': '/selecttwo/library/pubtype/name/icontains',
    'data_add_modalurl':  '/library/form/pubtype/main/',
    'data_add_displayfield': 'name'
}

class PublicationSearchForm(forms.Form):

    class Meta:
        model = Publication
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(PublicationSearchForm, self).__init__(*args, **kwargs)

        try:
            tag_id_choices = [(choice.pk, choice.name) for choice in
                              Tag.objects.filter(pk__in=[int(i) for i in self.data.getlist('tag__id')])]
        except:
            tag_id_choices = []
        self.fields['tag__id'] = MultipleChoiceField(
                label=_("Tag"),
                required=False,
                choices=tag_id_choices,
                initial=tag_id_choices
        )

        self.fields['sector__path'] = forms.MultipleChoiceField(
                required=False,
                label=_("Sectors"),
                choices=[(i.lowerpathstring(), i.name) for i in PropertyTag.objects.filter(path__startswith="INV.")]
        )

        self.fields['organization'] = forms.MultipleChoiceField(
                choices=Publication.objects.all().select_related('organization').values_list(
                        'organization__pk', 'organization__name').distinct().order_by('organization__name'),
                required=False,
                label=_("Organization(s)")
        )
        self.fields['year'] = forms.MultipleChoiceField(
                required=False,
                label=_("Year(s)"),
                choices=Publication.objects.order_by(
                        'year').values_list('year', 'year').distinct(),
                help_text="Select two years to find all publications between them",
        )
    text = forms.CharField(required=False)



    pubtype = forms.MultipleChoiceField(
            required=False,
            label=_("Type(s)"),
            # choices=Pubtype.objects.all().excdlude(code='pri').values_list('pk', 'name')
            choices=[]
    )

    primary = forms.BooleanField(
            required=False,
            label=_("Include primary sources")
    )
    # location = forms.MultipleChoiceField(
    #     label=_('Location'),
    #     required=False,
    #     choices=((0, 'Sorry - not yet implemented'),)
    # )

    language_id = forms.MultipleChoiceField(
            label=_('Language'),
            required=False,
            choices=LANGUAGES_FIX_ID
    )

    # country = forms.MultipleChoiceField(
    #     label=_('Country'),
    #     required=False,
    #     choices=((0, 'Sorry - not yet implemented'),)
    # )

    @property
    def helper(self):

        helper = FormHelper()
        helper.form_class = 'form-horizontal datacenter-search-form'
        helper.label_class = 'col-lg-4'
        helper.field_class = 'col-lg-8'
        helper.form_method = 'get'
        helper.wrapper_class = 'form-group-sm col-lg-6 col-md-6 col-sm-12 row'
        helper.layout = Layout(
                Fieldset(_("Search for Publications"),
                         Field('tag__id', wrapper_class=helper.wrapper_class,
                               data_selecturl="/selecttwo/library/tag/name/icontains/"),
                         Field('text', wrapper_class=helper.wrapper_class),
                         Field('organization', wrapper_class=helper.wrapper_class),
                         Field('sector__path', wrapper_class=helper.wrapper_class),
                         # Field('inv', wrapper_class=self.helper.wrapper_class),
                         Field('pubtype', wrapper_class=helper.wrapper_class),
                         Field('language_id', wrapper_class=helper.wrapper_class),
                         Field('year', wrapper_class=helper.wrapper_class, attrs={'maxItems': 2}),
                         Field('primary', wrapper_class=helper.wrapper_class),
                         ),
                Submit('search', u_('Search'), css_class="btn btn-success btn"),
        )
        return helper


class PubtypeForm(SuggestionForm):
    class Meta:
        model = Pubtype
        exclude = []

    def __init__(self, pubtype=None, *args, **kwargs):
        super(PubtypeForm, self).__init__(pubtype, *args, **kwargs)
        self.instance = pubtype

    @property
    def helper(self):
        helper = self.get_helper()
        helper.layout.extend(['code', 'name'])
        return helper


class PublicationForm(SuggestionForm):

    class Meta:
        model = Publication
        exclude=[]

    def __init__(self, publication=None, *args, **kwargs):
        super(PublicationForm, self).__init__(publication, *args, **kwargs)
        self.instance = publication

    @property
    def helper(self):
        helper = self.get_helper()
        a = [AccordionGroup(n, "name_"+c, "description_"+c) for c, n in LANGUAGES_FIX_ID]
        helper.layout.extend([
            'year',
            Field('pubtype',
                  # data_selecturl='/selecttwo/library/pubtype/name/icontains',
                  placeholder='Publication Type',
                  style='width:75%;', **create_pubtype_elements),
            Accordion(*a)])
        return helper


class PublicationOrganizationForm(SuggestionForm):
    class Meta:
        model = Publication
        fields = ["organization"]

    def __init__(self, publication, *args, **kwargs):
        super(PublicationOrganizationForm, self).__init__(publication, *args, **kwargs)
        self.instance = publication
        self.set_field_opts(name=['organization'], instance = self.instance)

    @property
    def helper(self):
        helper = self.get_helper()

        helper.layout.extend([
            Field('organization',
                  data_selecturl='/selecttwo/nhdb/organization/name/icontains',
                  placeholder='organization',
                  style='width:75%;', **create_organization_elements), Hidden('has_many', 'author')])

        return helper


class PublicationAuthorForm(SuggestionForm):
    class Meta:
        model = Publication
        fields = ["author"]

    def __init__(self, publication=None, *args, **kwargs):
        super(PublicationAuthorForm, self).__init__(_instance=publication, *args, **kwargs)
        self.instance = publication
        self.set_field_opts(name=['author'], instance = self.instance)

    @property
    def helper(self):
        helper = self.get_helper()
        helper.layout.extend([
            Field('author',
                  data_selecturl='/selecttwo/library/author/name/icontains',
                  placeholder='author',
                  style='width:75%;', **create_author_elements), Hidden('has_many', 'author')])
        return helper


class AuthorForm(SuggestionForm):
    class Meta:
        model = Author
        exclude = []

    def __init__(self, author=None, *args, **kwargs):
        super(AuthorForm, self).__init__(author, *args, **kwargs)
        self.author = author

    @property
    def helper(self):
        helper = self.get_helper()
        helper.layout.append(Field('name'))
        helper.layout.append(Field('displayname'))
        return helper


class VersionForm(SuggestionForm):
    class Meta:
        model = Version
        # fields = ('title','title_tet', 'description','upload','cover','url','publication')
        exclude = []

    def __init__(self, version=None, publication=None, *args, **kwargs):
        assert version or publication

        super(VersionForm, self).__init__(version, *args, **kwargs)
        self.version = version
        self.publication = publication
        self.set_field_opts(name=['publication'], instance=version)

    @property
    def helper(self):
        helper = self.get_helper()
        helper.layout.append('publication')
        helper.layout.extend([
            TranslationTabs(fieldnames=('title', 'description', 'upload', 'cover', 'url')).tabholder,
        ])

        return helper


class VersionUpdateForm(SuggestionForm):
    class Meta:
        model = Version
        fields = ['publication', 'title', 'description', 'upload', 'cover', 'url']

    def __init__(self, version=None, *args, **kwargs):
        super(VersionUpdateForm, self).__init__(version, *args, **kwargs)
        self.fields['publication'].choices = []
        self.instance = version

    @property
    def helper(self):
        helper = self.get_helper()
        helper.layout.extend([
            Field('publication',
                  data_selecturl='/selecttwo/library/publication/name/icontains',
                  placeholder='publication',
                  style='width:75%;'),
            TranslationTabs(fieldnames=('title', 'description', 'upload', 'cover', 'url')).tabholder,
        ])
        return helper
