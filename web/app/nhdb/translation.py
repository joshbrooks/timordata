from modeltranslation.translator import register, TranslationOptions
from nhdb.models import PropertyTag, Project, Organization


@register(PropertyTag)
class PropertyTagTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)


@register(Project)
class ProjectTranslation(TranslationOptions):
    fields = ('notes',)


@register(Organization)
class OrganizationTranslation(TranslationOptions):
    fields = ('description',)
