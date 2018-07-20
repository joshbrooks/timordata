from django.contrib import admin
from django.core.exceptions import ValidationError
from modeltranslation.admin import TranslationAdmin
from nhdb.models import *
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count
from django.core.validators import validate_email
import string
import logging

logger = logging.getLogger(__name__)


class AlphabetFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        return zip(string.uppercase, string.uppercase)


class NameListFilter(AlphabetFilter):
    title = _("Name")
    parameter_name = "name"

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(name__startswith=self.value)


class FirstNameListFilter(AlphabetFilter):
    # Human-readable title
    title = _("First Name")
    parameter_name = "firstname"

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(contact__first__startswith=self.value)


class LastNameListFilter(AlphabetFilter):
    # Human-readable title
    title = _("Last Name")
    parameter_name = "lastname"

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(contact__last__startswith=self.value)


class PersonFirstNameListFilter(AlphabetFilter):
    # Human-readable title
    title = _("First Name")
    parameter_name = "firstname"

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(name__startswith=self.value())


#
# class PersonLastNameListFilter(AlphabetFilter):
#     # Human-readable title
#     title = _('Last Name')
#     parameter_name = 'lastname'
#
#     def queryset(self, request, queryset):
#         if self.value():
#
#             return queryset.filter(name__last__startswith=self.value)


class NumberOfStaffFilter(admin.SimpleListFilter):
    title = _("Staff")
    parameter_name = "staff"

    def lookups(self, request, model_admin):
        count = ["0", "2", "5", "10", "20", "gt20"]
        labels = ["None", "0 to 2", "2 to 5", "5 to 10", "10 to 20", "More than 20"]
        return zip(count, labels)

    def queryset(self, request, queryset):

        queryset.annotate(num_staff=Count("person"))

        if self.value() == "0":
            return queryset.filter(num_staff=0)
        elif self.value() == "2":
            return queryset.filter(num_staff__gt=0).filter(num_staff__lte=2)
        elif self.value() == "5":
            return queryset.filter(num_staff__gt=2).filter(num_staff__lte=5)
        elif self.value() == "10":
            return queryset.filter(num_staff__gt=5).filter(num_staff__lte=10)
        elif self.value() == "20":
            return queryset.filter(num_staff__gt=10).filter(num_staff__lte=20)
        elif self.value() == "gt20":
            return queryset.filter(num_staff__gt=20)
        else:
            return queryset


class NumberOfProjectsFilter(admin.SimpleListFilter):
    title = _("No. of Projects")
    parameter_name = "projects"

    def lookups(self, request, model_admin):
        count = [0, 2, 5, 10, 20, "gt20"]
        labels = ["None", "0 to 2", "2 to 5", "5 to 10", "10 to 20", "More than 20"]
        return zip(count, labels)

    def queryset(self, request, queryset):

        queryset.annotate(num_projects=Count("project"))

        if self.value() == "0":
            return queryset.filter(num_projects=0)
        elif self.value() == "2":
            return queryset.filter(num_projects__gt=0).filter(num_projects__lte=2)
        elif self.value() == "5":
            return queryset.filter(num_projects__gt=2).filter(num_projects__lte=5)
        elif self.value() == "10":
            return queryset.filter(num_projects__gt=5).filter(num_projects__lte=10)
        elif self.value() == "20":
            return queryset.filter(num_projects__gt=10).filter(num_projects__lte=20)
        elif self.value() == "gt20":
            return queryset.filter(num_projects__gt=20)
        else:
            return queryset


class PersonAdmin(admin.ModelAdmin):
    # form = PersonAdminForm
    list_display = ("name",)
    raw_id_fields = ("organization",)
    autocomplete_lookup_fields = {"fk": ["organization"]}
    list_filter = (PersonFirstNameListFilter,)  # , PersonLastNameListFilter)

    # form = PersonInlineAdminForm


class ProjOrgInline(admin.TabularInline):

    model = ProjectOrganization
    raw_id_fields = ("project", "organization")
    #  radio_fields = {'organizationclass': admin.HORIZONTAL}
    extra = 1
    autocomplete_lookup_fields = {"fk": ["organization"]}


class ProjectAdmin(TranslationAdmin):
    search_fields = ("name", "name_en")
    raw_id_fields = ("sector", "activity", "beneficiary")
    autocomplete_lookup_fields = {"m2m": ["sector", "activity", "beneficiary"]}
    inlines = [ProjOrgInline]


class OrganizationAdmin(TranslationAdmin):

    exclude = ["description_en", "description_pt", "description_tet", "description_id"]

    class PersonInline(admin.TabularInline):
        model = Person

    class ProjOrgInline(admin.TabularInline):

        model = ProjectOrganization
        autocomplete_lookup_fields = {
            # 'm2m': ['sector', 'activity', 'beneficiary'],
            "fk": ["project"]
        }
        raw_id_fields = ("project", "organization")
        radio_fields = {"organizationclass": admin.HORIZONTAL}
        extra = 1

    inlines = [ProjOrgInline, PersonInline]
    list_filter = (
        "orgtype",
        "active",
        NumberOfStaffFilter,
        NameListFilter,
        NumberOfProjectsFilter,
    )

    radio_fields = {"orgtype": admin.HORIZONTAL}


admin.site.register(Project, ProjectAdmin)
admin.site.register(Organization)
admin.site.register(Person, PersonAdmin)
admin.site.register(ProjectImage)
admin.site.register(ProjectPlace)
admin.site.register(ProjectOrganization)
admin.site.register(PropertyTag)
admin.site.register(ProjectPerson)
