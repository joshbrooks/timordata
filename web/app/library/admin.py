from django.contrib import admin
from django import forms
from library.models import Publication, Version, Tag, Author, Pubtype
# Register your models here.

from modeltranslation.admin import TranslationAdmin, TranslationStackedInline
from modeltranslation.translator import translator


class VersionInline(TranslationStackedInline):
    model = Version
    raw_id_fields = ('tag','sector','beneficiary','activity')
    autocomplete_lookup_fields = {
        # 'fk': ['organization'],
        'm2m': ['tag','sector','beneficiary','activity']
    }


class PublicationAdmin(TranslationAdmin):
    raw_id_fields = ('organization','author','location','country')
    autocomplete_lookup_fields = {
        # 'fk': ['organization'],
        'm2m': ['organization','author','location','country','tag','sector','beneficiary','activity'],
    }
    inlines = [
        VersionInline,
    ]


class VersionAdmin(TranslationAdmin):
    raw_id_fields = ('publication','tag')
    autocomplete_lookup_fields = {
        'fk': ['publication'],
        'm2m': ['tag'],
    }


admin.site.register(Publication, PublicationAdmin)
admin.site.register(Tag)
admin.site.register(Version, VersionAdmin)
admin.site.register(Author)
admin.site.register(Pubtype)
