
from modeltranslation.translator import translator, TranslationOptions
from library.models import Version, Publication, Pubtype, Tag


class PublicationTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class VersionTranslationOptions(TranslationOptions):
    fields = ('description','title','upload','cover','url')


class PubtypeTranslationOptions(TranslationOptions):
    fields = ('name',)


class Tagtranslation(TranslationOptions):
    fields = ('name',)


translator.register(Version, VersionTranslationOptions)
translator.register(Pubtype, PubtypeTranslationOptions)
translator.register(Tag, Tagtranslation)
translator.register(Publication, PublicationTranslationOptions)