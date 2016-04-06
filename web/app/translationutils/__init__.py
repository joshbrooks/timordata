def get_translated_fields(cls, prefix='title'):
    from modeltranslation.fields import TranslationField as TF
    return [i.name for i in cls._meta.fields if i.name.startswith(prefix) and isinstance(i, TF)]

