from django.contrib import admin

# Register your models here.
from donormapping.models import (
    DonorAnnouncement,
    FundingOffer,
    FundingSurveyInfoMethods,
    FundingSurvey,
    DonorSurveyResponse,
    FundingOfferDocument,
)


class FileInline(admin.TabularInline):
    model = FundingOfferDocument


class FundingOfferAdmin(admin.ModelAdmin):
    raw_id_fields = ("sector", "activity", "beneficiary", "organization")
    autocomplete_lookup_fields = {
        "fk": ("organization",),
        "m2m": ("sector", "activity", "beneficiary"),
    }

    inlines = [FileInline]


class DonorSurveyResponseAdmin(admin.ModelAdmin):
    raw_id_fields = ("organization",)
    autocomplete_lookup_fields = {"fk": ("organization",)}
    list_filter = ("response",)


class DonorAnnouncementAdmin(admin.ModelAdmin):
    raw_id_fields = ("source",)
    autocomplete_lookup_fields = {"fk": ("source",)}


admin.site.register(FundingOffer, FundingOfferAdmin)
admin.site.register(FundingSurveyInfoMethods)
admin.site.register(FundingSurvey)
admin.site.register(DonorSurveyResponse, DonorSurveyResponseAdmin)
admin.site.register(DonorAnnouncement, DonorAnnouncementAdmin)
