from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Hidden, Submit, HTML, Field, Button
from django import forms
from django.forms import ModelForm
from suggest.models import Suggest, get_field_type, is_many_to_many, logger

__author__ = 'josh'

__all__ = []


def getsubmiturl(base_url, instance):
    pass


def manyfieldlayout(instance):
    '''
    Return a Layout of HiddenFields for any many-to-many relations
    '''
    return Layout(*[Hidden('has_many', f.name) for f in instance._meta.many_to_many])


def choose_or_create(*args, **kwargs):
    layout = Layout()

    fieldname = kwargs.get('fieldname', 'organization')
    data_selecturl = kwargs.get('data_selecturl', '/selecttwo/nhdb/project/name/icontains')
    data_modalurl = kwargs.get('data_modalurl', '/nhdb/form/organization/main/')
    layout.append(Field(fieldname, data_selecturl=data_selecturl, placeholder=fieldname, style='width:70%;'))
    layout.append(Button('Add', 'Add a new %s' % (fieldname), style='width:25%;', data_modalurl=data_modalurl))
    return layout


class DeleteFormHelper(FormHelper):

    def __init__(self, instance, url=None, css_class='btn-sm btn-warning', buttontext='Delete', alert=None):

        errormessage = '<div class="alert alert-danger" role="alert"><strong>Please confirm: </strong> You are about to remove <strong>{}</strong> from the database</div>'

        app, mod, pk = instance._meta.app_label, instance._meta.model_name, instance.pk
        submit_url = url or '/rest/{}/{}/{}/'.format(app, mod, pk)

        if not instance.pk:
            raise TypeError('Cannot create a DeleteForm for an uninitialised object: {}'.format(instance))

        # The URL can be specified manually but if not given, is automatically tried from '/rest/app/model/pk/'

        super(DeleteFormHelper, self).__init__()
        self.attrs = {'action': '/suggest/suggest/'}
        self.form_method = 'POST'
        self.layout = Layout(
            Hidden('_method', 'DELETE'),
            Hidden('_url', submit_url),
            Hidden('_action', 'DM'),
            Hidden('_description', 'Remove {} from the database'.format(instance)),
            Hidden('_affected_instance_primary', '{}_{} {}'.format(app, mod, pk)),
            # FormActions(
            #     Submit('__action', buttontext, css_class=css_class+' hidden'),
            # ))
        )
        if alert is True:
            try:
                self.layout.append(
                    HTML(errormessage.format(instance))
                )
            except:
                self.layout.append(
                    HTML(errormessage.format('an object'))
                )
        elif isinstance(alert, str):
            try:
                self.layout.append(
                    HTML(errormessage.format(alert))
                )
            except:
                self.layout.append(
                    HTML(errormessage.format('an object'))
                )
        elif alert:
            self.layout.append(
                HTML(errormessage.format(alert))
            )


class CreateFormHelper(FormHelper):

    def __init__(self, instance=None, model=None, url=None, **kwargs):

        try:

            if instance:
                app, mod = instance._meta.app_label, instance._meta.model_name
                name = instance._meta.verbose_name
                submit_url = url or '/rest/{}/{}/'.format(app, mod)
                description = kwargs.get('description', 'Create a new {} in the database'.format(name))

                if instance.pk:
                    raise TypeError('Cannot create a CreateFormHelper for an exiting object')

            elif model:
                app, mod = model._meta.app_label, model._meta.model_name
                name = model._meta.verbose_name
                submit_url = url or '/rest/{}/{}/'.format(app, mod)
                description = kwargs.get('description', 'Create a new {} in the database'.format(name))

            else:
                app, mod = 'Exception', 'Exception'
                name = 'Exception'
                submit_url = 'Exception'
                description = 'Exception: No instance or model supplied'

            super(CreateFormHelper, self).__init__()
            self.attrs = {'action': '/suggest/suggest/'}
            self.form_method = 'POST'
            self.layout = Layout(
                Hidden('_method', 'POST'),
                Hidden('_url', submit_url),
                Hidden('_action', 'CM'),
                Hidden('_description', description),
                Hidden('_affected_instance_primary', '{}_{}'.format(app, mod)),
                Hidden('__formtype', "Create Form"),
                Hidden('_next', '/suggest/#object=_suggestion_'),
                manyfieldlayout(instance),
                Layout(*[Hidden('__nochange', f) for f in kwargs.get('nochange', [])]),
            )

        except Exception as e:

            self.layout = Layout(HTML('<p>{}</p>'.format(e.message)))


class UpdateFormHelper(FormHelper):

    def __init__(self, instance=None, suggestion=None, url=None, description=None, *args, **kwargs):

        try:

            super(UpdateFormHelper, self).__init__()

            if hasattr(instance, '_meta') and hasattr(instance, 'pk'):
                app = instance._meta.app_label
                mod = instance._meta.model_name
                pk = getattr(instance, 'pk')
                name = instance._meta.verbose_name
                aip = Hidden('_affected_instance_primary', '{}_{} {}'.format(app, mod, pk))

            elif hasattr(suggestion, 'primary') and hasattr(suggestion, 'pk'):
                app, mod = suggestion.primary.model_name.split('_')
                name = "suggestion"
                pk = '_%s_' % (getattr(suggestion, 'pk'))
                instance = "suggestion"
                aip = Hidden('_affected_instance_primary', '{}_{} {}'.format('suggest', 'suggest', getattr(suggestion, 'pk')))

            else:
                raise AssertionError('Supply either a Suggestion or a model instance')

            if not description:
                description = kwargs.get('description', 'Modify a {} ({}) in the database'.format(name, instance))

            submit_url = url or '/rest/{}/{}/{}/'.format(app, mod, pk)

            self.attrs = {'action': '/suggest/suggest/'}
            self.form_method = 'POST'
            self.form_tag = True
            self.layout = Layout(
                Hidden('_method', 'PATCH'),
                Hidden('_url', submit_url),
                Hidden('_action', 'UM'),
                Hidden('_description', description),
                Hidden('__formtype', "Update Form"),
                manyfieldlayout(instance),
                aip)

        except Exception as e:
            super(UpdateFormHelper, self).__init__()
            self.layout = Layout()
            self.layout.extend([HTML('''<div class="alert alert-{}" role="alert">{}</div>'''.format('warning', e.message))])
            raise


class UpdateSuggestionHelper(FormHelper):

    def __init__(self, suggestion=None, url=None, description=None, *args, **kwargs):
        try:
            super(UpdateSuggestionHelper, self).__init__(*args, **kwargs)
            #  TODO: Assert that the model to be changed is the same as the instance
            submit_url = None
            name = None

            instance = suggestion.primary.instance

            if url:
                submit_url = kwargs.get('url')
            if instance:
                meta = instance._meta
                app, mod, name = meta.app_label, meta.model_name, meta.verbose_name

                if instance.pk and not submit_url:
                    submit_url = '/rest/{}/{}/{}/'.format(app, mod, instance.pk)

            if suggestion and not submit_url:

                if suggestion.state != 'A':

                    model = suggestion.primary.retrieve_model
                    i = model()
                    app, mod, name = i._meta.app_label, i._meta.model_name, i._meta.verbose_name
                    submit_url = '{}_{}_/'.format(suggestion.url, suggestion.pk)

                else:
                    submit_url = suggestion.url

            else:
                if not submit_url:
                    submit_url = suggestion.url + 'ERROR - might not be a primary instance?'

            self.attrs = {'action': '/suggest/suggest/'}
            self.form_method = 'POST'
            self.layout = Layout(
                Hidden('_method', 'PATCH'),
                Hidden('_url', submit_url),
                Hidden('_action', 'UM'),
                Hidden('_description', kwargs.get('description') or 'Modify a {} in the database'.format(name)),
                Hidden('_affected_instance_primary', 'suggest_suggest {}'.format(suggestion.pk)),
                Hidden('_next', '/suggest/#object=_suggestion_'),
                manyfieldlayout(instance),
                Layout(*[Hidden('__nochange', f) for f in kwargs.get('nochange', [])]),
                # HTML('''<div class="alert alert-{}" role="alert">{}</div>'''.format('info', 'UpdateSuggestionHelper loaded successfully'))
            )

        except Exception as e:
            super(UpdateSuggestionHelper, self).__init__(*args, **kwargs)
            self.layout = Layout()
            self.layout.extend([HTML('''<div class="alert alert-{}" role="alert">{}</div>'''.format('warning', e.message))])
            self.layout.extend([HTML('''<div class="alert alert-{}" role="alert">{}</div>'''.format('warning', 'UpdateSuggestionHelper'))])
            raise


class SuggestionDeleteForm(forms.ModelForm):
    '''
    Renders a form to suggest deleting an suggestion
    '''

    class Meta:
        fields = ()
        model = Suggest

    def __init__(self, instance, *args, **kwargs):
        if 'nochange' in kwargs:
            kwargs.pop('nochange')
        super(SuggestionDeleteForm, self).__init__(instance=instance, *args, **kwargs)
        self.instance = instance

    def get_helper(self):
        helper = DeleteFormHelper(instance=self.instance)
        helper.layout.append(HTML(
            '<div class="alert alert-danger" role="alert"><strong>Please confirm: </strong> You are about to remove <strong>{}</strong> from the database</div>'.format(
                self.instance)))
        return helper

    @property
    def helper(self):
        return self.get_helper()


class SuggestDeleteForm(forms.ModelForm):
    '''
    Renders a form to suggest deleting an object
    '''

    def __init__(self, instance, *args, **kwargs):
        super(SuggestDeleteForm, self).__init__(*args, **kwargs)
        self.instance = instance

    @property
    def helper(self):
        helper = DeleteFormHelper(instance=self.instance)
        helper.layout.append(Hidden('__primary_key_field', self.instance.model._meta.pk.name))
        return helper


class MessageFormHelper(FormHelper):
    '''
    Returns a FormHelper with a bootstrap message
    :return:
    '''

    def __init__(self, message, cssclass="warning", *args, **kwargs):
        #  Possible cssclass values for bootstrap are success, info, warning, and danger
        super(MessageFormHelper, self).__init__(*args, **kwargs)
        self.layout = Layout()
        self.layout.extend([HTML('''<div class="alert alert-{}" role="alert">{}</div>'''.format(cssclass, message))])


class SuggestionForm(forms.ModelForm):

    def __init__(self, _instance, *args, **kwargs):

        instance = _instance
        self.suggest = None

        if instance is None:
            self.instance = None

        elif isinstance(instance, Suggest):
            self.suggest = instance
            setattr(self, 'instance', None)

        elif isinstance(instance, self.Meta.model):
            self.suggest = None
            self.instance = instance

        else:
            raise TypeError('_instance should be a %s or a Suggest object - got %s' % (self.Meta.model._meta.model_name, type(_instance)))

        self.nochange = kwargs.pop('nochange', ['no-fixed-attributes'])

        super(SuggestionForm, self).__init__(instance=instance, *args, **kwargs)

        # Update fields where an existing suggestion is being modified
        if isinstance(_instance, Suggest):
            for i, j in list(_instance.data_jsonify().items()):
                if i in self.fields:
                    self.fields[i].initial = j

    def get_wrapper_class(self, field_name):
        if field_name in self.nochange:
            return 'hidden'
        else:
            return None

    def get_helper(self, **kwargs):

        if isinstance(self.suggest, Suggest):
            helper = UpdateSuggestionHelper(suggestion=self.suggest)
        elif hasattr(self, 'instance') and self.instance is not None and self.instance.pk is not None:
            helper = UpdateFormHelper(instance=self.instance, **kwargs)
            helper.layout.append(Layout(*[Hidden('__nochange', f) for f in self.nochange])),
        elif self.instance is None:
            helper = CreateFormHelper(instance=self.Meta.model(), **kwargs)
        else:
            helper = CreateFormHelper(instance=self.Meta.model(), **kwargs)

        helper.form_class = 'form-horizontal'
        helper.form_id = self.Meta.model._meta.model_name + '-form'
        helper.label_class = 'col-lg-3'
        helper.field_class = 'col-lg-9'
        # Fields not named "id" should be explicitly identified here
        helper.layout.append(Hidden('__primary_key_field', self.Meta.model._meta.pk.name))

        return helper

    @property
    def helper(self):
        return self.get_helper()

    def set_field_opts(self, name=[], instance=None, **kwargs):
        """
        Modofy the choices available (i.e. prepare to replace with a select2 field)
        :param name:
        :return:
        """

        logger.warn('set_field_opts')
        logger.warn('%s %s %s' % (name, instance, kwargs))

        if isinstance(name, str):
            name = [name]

        for _n in name:
            choices = []

            if isinstance(instance, Suggest):

                if not instance.follow(_n):
                    return choices
                for i in instance.follow(_n):
                    if isinstance(i, Suggest):
                        choices.append(('_%s_' % (i.pk), '%s' % (i)))
                    else:
                        choices.append(('%s' % (i.pk), '%s' % (i)))
                self.fields[_n].choices = choices
                continue

            else:
                try:

                    # First from "instance"; then from "self"; then from any kwargs passed to the function

                    # if instance and hasattr(instance, _n):
                    n = getattr(instance, _n, None) or getattr(self, _n, None) or kwargs.get(_n, None)

                    if not n:
                        continue

                    if isinstance(n, Suggest):
                        self.fields[_n].choices = [('_{}_'.format(n.pk), n)]

                    elif hasattr(n, 'pk'):
                        self.fields[_n].choices = [(n.pk, n)]

                    elif instance and is_many_to_many(instance, _n):
                        self.fields[_n].choices = [(p.pk, '%s' % (p)) for p in n.all()]

                    else:
                        self.fields[_n].choices = []

                except KeyError as e:
                    raise KeyError('%s not in fields: %s' % (_n, list(self.fields.keys())))

                except AttributeError as e:
                    raise AttributeError('There was a problem adding %s %s to the choices available' % (_n, n))

                except:
                    raise
