__author__ = 'josh'
from modeltranslation.translator import register, TranslationOptions
from nhdb.models import *

@register(PropertyTag)
class PropertTagTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

@register(Project)
class ProjectTranslation(TranslationOptions):
    fields = ('name', 'description', 'notes')

@register(Organization)
class OrganizationTranslation(TranslationOptions):
    fields = ('description',)