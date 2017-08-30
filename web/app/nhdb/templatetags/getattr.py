from django import template
register = template.Library()


@register.filter
def getattr(obj, args):
    """ Try to get an attribute from an object.

    Example: {% if block|getattr:"editable,True" %}

    Beware that the default is always a string, if you want this
    to return False, pass an empty second argument:
    {% if block|getattr:"editable," %}
    """
    (attribute, default) = args.split(',')
    args = args.split(',')
    if len(args) == 1:
        (attribute, default) = [args[0], '']
    else:
        (attribute, default) = args
    try:
        return obj.__getattribute__(attribute)
    except AttributeError:
        return obj.__dict__.get(attribute, default)
    except:
        return default


@register.filter
def getname(obj, languagecode):
    """ Try to get a translated field from an object
    """
    default = 'Error getting translated field'
    try:
        return obj.__getattribute__('name_' + languagecode) or ''
    except AttributeError:
        return obj.__dict__.get('name', default)
    except:
        return default


@register.filter
def getdescription(obj, languagecode):
    """ Try to get a translated field from an object
    """
    default = 'Error getting translated field'
    try:
        return obj.__getattribute__('description_' + languagecode) or ''
    except AttributeError:
        return obj.__dict__.get('description', default)
    except:
        return default


@register.filter
def getnotes(obj, languagecode):
    """ Try to get a translated field from an object
    """
    default = 'Error getting translated field'
    try:
        return obj.__getattribute__('notes_' + languagecode) or ''
    except AttributeError:
        return obj.__dict__.get('notes', default)
    except:
        return default
