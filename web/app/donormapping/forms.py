# -*- coding: utf-8 -*-
from django import forms
from django.db.models import Count
from geo.models import District
from .models import FundingOffer, FundingSurvey, FundingOfferDocument
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Field, Fieldset, HTML, Hidden
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as u_
from nhdb.models import PropertyTag, Organization
from suggest.forms import SuggestionForm, choose_or_create
from suggest.models import Suggest


class FundingSurveyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FundingSurveyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-5"
        self.helper.field_class = "col-lg-7"
        self.helper.form_id = "id-exampleForm"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    "Details", "organizationname", "organisationtype", "properties"
                ),
                css_class="col-md-12 well",
            ),
            Div(
                Fieldset(
                    _("Questions for Recipients"),
                    "fundingreceived",
                    "fundingrecvamt",
                    "fundingrecvrel",
                    "fundingrecvmethod",
                    "qfunding",
                    "qtransport",
                    "qprocess",
                    "qdonorsector",
                ),
                css_class="col-md-6 well",
            ),
            Div(
                Fieldset(
                    _("Questions for Donors"),
                    "fundinggiven",
                    "fundinggiveamt",
                    "fundinggiverel",
                    "fundinggivemethod",
                    "qrecipients",
                ),
                css_class="col-md-5 col-md-offset-1 well",
            ),
            Div(
                Fieldset(
                    _("Technology Access"),
                    "usefacebook",
                    "usegmail",
                    "usegoogle",
                    "hascomputer",
                ),
                "hasprinter",
                "hasmobile",
                "hassmartphone",
                css_class="col-md-5 col-md-offset-1 well",
            ),
            Div(Submit("submit", "Submit"), css_class="col-md-12"),
        )

    class Meta:
        model = FundingSurvey
        exclude = []


class FundingOfferDocumentForm(SuggestionForm):
    class Meta:
        model = FundingOfferDocument
        exclude = []
        instance_name = "FundingOfferDocument".lower()

    def __init__(self, fundingofferdocument=None, fundingoffer=None, *args, **kwargs):

        if hasattr(self.Meta, "instance_name"):
            _instance = locals().get(getattr(self.Meta, "instance_name"))
        else:
            _instance = locals().get(self.Meta.model._meta.model_name)

        self.fundingofferdocument, self.fundingoffer = (
            fundingofferdocument,
            fundingoffer,
        )

        super(FundingOfferDocumentForm, self).__init__(
            _instance=_instance, *args, **kwargs
        )

        if fundingoffer:
            if isinstance(fundingoffer, Suggest):
                self.fields["offer"].choices = [
                    ("_%s_" % (fundingoffer.pk), fundingoffer)
                ]
            elif isinstance(fundingoffer, FundingOffer):
                self.fields["offer"].choices = [
                    ("%s" % (fundingoffer.pk), fundingoffer)
                ]

    @property
    def helper(self):
        helper = self.get_helper()

        helper.layout.append(Field("file"))
        helper.layout.append(Field("description"))
        if self.fundingoffer:
            helper.layout.append(
                Field("offer", css_class="hidden", wrapper_class="hidden")
            )
        else:
            helper.layout.append(Field("offer"))

        return helper


class FundingOfferForm(SuggestionForm):
    class Meta:
        model = FundingOffer
        exclude = []

    def __init__(self, fundingoffer=None, suggest=None, *args, **kwargs):

        if hasattr(self.Meta, "instance_name"):
            _instance = locals().get(getattr(self.Meta, "instance_name"))
        else:
            _instance = locals().get(self.Meta.model._meta.model_name)

        self.fundingoffer = fundingoffer

        super(FundingOfferForm, self).__init__(_instance=_instance, *args, **kwargs)

        if isinstance(self.fundingoffer, FundingOffer):
            self.fields["organization"].choices = [
                (
                    self.fundingoffer.organization.pk,
                    "%s" % self.fundingoffer.organization,
                )
            ]
        elif isinstance(self.fundingoffer, Suggest):
            o = Organization.objects.get(self.fundingoffer.follow("organization"))
        else:
            self.fields["organization"].choices = []

    @property
    def helper(self):

        create_organization_elements = {
            "data_add_selecturl": "/selecttwo/nhdb/project/name/icontains",
            "data_add_modalurl": "/nhdb/form/organization/main/",
            "data_add_modalselector": "#stack2",
            "data_add_displayfield": "name",
        }

        select_kwargs = {
            "wrapper_class": "col-lg-12 col-md-12 col-sm-12",
            "style": "padding-left:20px; padding-right:20px;",
        }

        try:
            helper = self.get_helper()
            helper.layout.extend(
                [
                    Div(
                        Field("title"),
                        Field(
                            "organization",
                            data_selecturl="/selecttwo/nhdb/organization/name/icontains",
                            **create_organization_elements
                        ),
                        Field("amount"),
                        Field("description", css_class="summernote"),
                        css_class="row",
                    ),
                    Div(
                        Fieldset(
                            "Target Sector, Activity and Beneficiary",
                            Field("sector", **select_kwargs),
                            Field("activity", **select_kwargs),
                            Field("beneficiary", **select_kwargs),
                            css_class="row",
                        )
                    ),
                ]
            )

        except Exception as e:
            helper = FormHelper()
            helper.layout = Layout()
            helper.layout.extend(
                [
                    HTML(
                        """<div class="alert alert-{}" role="alert">{}</div>""".format(
                            "warning", e.message
                        )
                    )
                ]
            )

        return helper


class FundingOfferSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(FundingOfferSearchForm, self).__init__(*args, **kwargs)

        self.fields["organization"] = forms.MultipleChoiceField(
            choices=FundingOffer.objects.all()
            .select_related("organization")
            .values_list("organization__pk", "organization__name")
            .distinct()
            .order_by("organization__name"),
            required=False,
            label=_("Organizations"),
        )

        self.fields["inv"] = forms.MultipleChoiceField(
            required=False,
            label=_("Sectors"),
            choices=[
                (i.lowerpathstring(), "{} ({})".format(i.name, i.count))
                for i in PropertyTag.objects.get(path="INV")
                .get_children()
                .annotate(count=Count("fundingoffer_sector"))
                .order_by("name")
                if i.count > 0
            ],
        )
        self.fields["ben"] = forms.MultipleChoiceField(
            required=False,
            label=_("Beneficiaries"),
            choices=[
                (i.lowerpathstring(), "{} ({})".format(i.name, i.count))
                for i in PropertyTag.objects.get(path="BEN")
                .get_children()
                .annotate(count=Count("fundingoffer_beneficiary"))
                .order_by("name")
                if i.count > 0
            ],
        )

        self.fields["act"] = forms.MultipleChoiceField(
            required=False,
            label=_("Activities"),
            choices=[
                (i.lowerpathstring(), "{} ({})".format(i.name, i.count))
                for i in PropertyTag.objects.get(path="ACT")
                .get_children()
                .annotate(count=Count("fundingoffer_activity"))
                .order_by("name")
                if i.count > 0
            ],
        )

        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-4"
        self.helper.field_class = "col-lg-8"
        self.helper.form_method = "get"
        self.helper.wrapper_class = "form-group-sm col-lg-4 col-md-6 col-sm-12 row"
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    u_("Type and Keywords"),
                    Field("organization", wrapper_class=self.helper.wrapper_class),
                    Field("act", wrapper_class=self.helper.wrapper_class),
                    Field("inv", wrapper_class=self.helper.wrapper_class),
                    Field("ben", wrapper_class=self.helper.wrapper_class),
                ),
                Submit("search", u_("Search"), css_class="btn btn-info btn"),
                css_class="col-md-12 well",
            )
        )

    try:
        district = forms.MultipleChoiceField(
            choices=District.objects.all()
            .values_list("pk", "name")
            .distinct()
            .order_by("name"),
            label=_("District"),
        )
    except:
        pass
