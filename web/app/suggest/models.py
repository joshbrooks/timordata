import datetime
import json

import collections
import logging

import warnings
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models import Q, FieldDoesNotExist
from django.db.models.base import ModelBase
from django.utils.safestring import mark_safe
import os
import re
from django.db import models, IntegrityError
from django.apps import apps
import dateutil.parser

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_field_type(obj, field_name):
    if isinstance(obj, ModelBase):
        obj = obj()
    try:
        field = obj.__class__._meta.get_field(field_name)
        return field.__class__.__name__
    except FieldDoesNotExist:
        raise KeyError, 'Field {} does not exist in this model'.format(field_name)


def is_foreign_key(obj, field_name):
    return get_field_type(obj, field_name) == 'ForeignKey'


def is_many_to_many(obj, field_name):
    return get_field_type(obj, field_name) == 'ManyToManyField'


def _get_model(app_model_name):
    try:
        app_label, model_name = app_model_name.split('_')
    except ValueError:
        raise ValueError('Looked for pattern (appname)_(modelname), did not find it in {}'.format(app_model_name))
    return apps.get_model(app_label=app_label, model_name=model_name)


class ReturnedData(unicode):
    # Wrapper to add 'ready' to the data
    def __init__(self, data):
        super(ReturnedData, self).__init__()
        self.ready = True
        self.data = data

    def __repr__(self):
        return self.data

    def __str__(self):
        return self.data


class SuggestionManager(models.Manager):
    def suggest(self, obj):
        '''
        Return suggested changes for the selected object instance
        '''

        model_name = '{}_{}'.format(obj._meta.app_label, obj._meta.model_name)

        return self.filter(
                affectedinstance__model_name=model_name,
                affectedinstance__model_pk=obj.pk)

    def independent(self):
        """
        Returns suggestions which are not dependent on anything else - they can
        be applied immediately

        EG a "Project" can be created immediately but a "ProjectPerson" dependent on that must wait until
        the Project suggestion has been created and the project PK is available
        """
        q = Q()
        q = q | Q(data__iregex='_(\d+)_')
        q = q | Q(url__iregex='_(\d+)_')
        return self.exclude(q)

    def dependent(self):
        """
        Returns suggestions which are dependent on another suggestion
        and cannot be applied immediately
        """
        q = Q()
        q = q | Q(data__iregex='_(\d+)_')
        q = q | Q(url__iregex='_(\d+)_')
        return self.filter(q)


class AffectedInstance(models.Model):
    """
    Keep a record of which models are going to be affected by the serializer's change
    For example a through field would affect two models
    e.g. ProjectPlace
    """
    model_name = models.CharField(max_length=128)
    suggestion = models.ForeignKey('suggest.Suggest')
    model_pk = models.CharField(max_length=128, null=True, blank=True)
    primary = models.BooleanField(default=False)

    # TODO: Make compatible with non integer PK's
    # model_pk_string = models.CharField(max_length=10, null=True, blank=True)

    def __unicode__(self):

        return 'From suggestion {} to change {} {} {}'.format(self.suggestion.id, self.model_name, self.model_pk,
                                                              self.primary)

    def related_changes(self):
        """
        Returns any items in "suggest" where the URL depends on the model_pk of the
        affected instance

        For example, a Project which has been suggested but does not have a primary key will
        have related_changes to project_organisation or projectplace and this will
        return those suggestions
        """
        return Suggest.objects.filter(url__icontains="_%s_" % (self.pk))

    def retrieve_model(self):

        try:
            return _get_model(self.model_name)
        except:
            return None

    def retrieve_instance(self):
        if not self.model_pk:
            instance = _get_model(self.model_name)()
            return instance
        model = _get_model(self.model_name)
        try:
            return model.objects.get(pk=self.model_pk)
        except model.DoesNotExist, e:
            raise model.DoesNotExist('{}: query was .get(pk={})'.format(e.message, self.model_pk))

    @property
    def instance(self):
        try:
            return self.retrieve_instance()
        except Exception, e:

            if self.suggestion.action and self.suggestion.state == 'A':
                return "Removed"
            else:
                self.suggestion.state = 'D'
                self.suggestion.skip_signal = True
                self.suggestion.save()
            return e.message


class SuggestUpload(models.Model):
    '''
    Allow anonymous users to safely upload files
    '''

    suggestion = models.ForeignKey('Suggest')
    field_name = models.CharField(max_length=256)
    upload = models.FileField(upload_to="suggestions", max_length=256, null=True, blank=True)


class Suggest(models.Model):
    '''
    Allow anonymous users to make suggestions which an admin user can "approve"
    Intended to integrate with the Django REST framework for a one-click "approve" option for models
    '''

    def __unicode__(self):
        # This is going to be different for each model
        # However if there is a "name", we can use that
        if self.action == 'CM':

            d = self.data_jsonify()
            parameter_try = ['name', 'name_en', 'name_tet', 'description', 'description_en', 'description_tet']

            for p in parameter_try:
                if d.get(p):
                    return "(New %s) %s" % (self.primary.model_name.split('_')[1], d.get(p))

                else:
                    return self.description or ''

        elif self.description:
            return self.description or ''

        return u'No description provided'

    OPTIONS_ACTION = (

        ('DR', 'Remove a relationship'),
        ('CR', 'Create a relationship'),
        ('UR', 'Update a relationship'),

        # Instead of the end user unfriendly "Model" use "entry"
        ('DM', 'Delete entry'),
        ('CM', 'Create entry'),
        ('UM', 'Update entry'),
    )

    OPTIONS_STATE = (
        ('W', 'Waiting Approval'),
        ('A', 'Accepted'),
        ('R', 'Rejected'),
        ('X', 'Flagged as never to show (contains inappropriate content / spam)'),
        ('E', 'Error occurred trying to approve this suggestion'),
        ('D', 'Error: Primary instance is missing or duplicate')
    )

    OPTIONS_METHOD = (
        ('DELETE', 'DELETE'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
    )

    name = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=2, choices=OPTIONS_STATE, default="W")
    action = models.CharField(max_length=128, choices=OPTIONS_ACTION, default="CM")
    is_hidden = models.BooleanField(default=False)
    # If the change is requested by a logged in user, remember the user name and ID
    user_name = models.CharField(max_length=128, blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    method = models.CharField(max_length=128, choices=OPTIONS_METHOD,
                              default="POST")  # PUT POST PATCH DELETE - action expected by REST api
    data = models.TextField(null=True, blank=True)  # json REPR of suggested changes to the primary model
    suggestDate = models.DateField(auto_now_add=True)
    approvalDate = models.DateField(null=True, blank=True)
    url = models.CharField(max_length=128)  # Django-REST API URL to push the change to when it's approved

    objects = SuggestionManager()

    def follow(self, key, strict=False):
        """
        Get a referenced model
        :param key:
        :return:
        """
        logger.debug('Following %s', key)

        def match(k, field):
            if not k:
                return
            k = str(k)

            if re.match('_(\w+)_', k):
                try:
                    _pk = k[1:-1]
                    logger.debug('Suggestion matched: %s', _pk)
                    suggestion = Suggest.objects.get(pk=_pk)
                    instance = suggestion.primary.instance
                    if instance.pk:
                        logger.debug('Returning instance  %s', instance)
                        return instance
                    else:
                        logger.debug('Returning suggestion  %s', suggestion)
                        return suggestion
                except:
                    logger.error('Oops on Following %s(%s)', key)
                    logger.error(self.data_jsonify)
                    # raise

            else:
                try:
                    to = field.field.rel.to
                    logger.debug('Field')
                    return to.objects.get(pk=k)
                except:
                    logger.error("Tried to follow '%s' from '%s' with pk '%s'", key, to, k)
                    logger.error(self.data_jsonify())
                    # raise

        def match_m2m(key_list, field):
            return [match(k, field) for k in key_list]

        p = self.primary
        while p.model_name == 'suggest_suggest':
            p = p.instance.primary

        m = _get_model(p.model_name)

        if key not in self.data_jsonify().keys():
            return

        k = self.data_jsonify().get(key)

        if get_field_type(m, key) not in ['ForeignKey', 'ManyToManyField']:
            logger.error('Field type is not valid: %s', get_field_type(m, key))
            if strict:
                raise TypeError('Field type is not valid: %s', get_field_type(m, key))
            return k
        else:
            field = getattr(m, key)

        if isinstance(k, list):
            return match_m2m(key_list=k, field=field)
        else:
            return match(k, field)

    @property
    def primary_key_field(self):
        """
        Fix for where primary key name is not "id"
        :return:
        """
        try:
            return self.primary.retrieve_model()._meta.pk.name
        except AffectedInstance.DoesNotExist:
            return None

    def perm(self, user):

        if not isinstance(user, User):
            return False

        try:
            primary = self.primary
        except:
            raise

        if not primary:
            return 'Nothing to act on'

        model_name = self.primary.model_name

        if self.action in ['DR', 'CR', 'UR', 'UM']:
            permission_name = model_name.replace('_', '.change_')
        elif self.action == 'DM':
            permission_name = model_name.replace('_', '.delete_')
        elif self.action == 'CM':
            permission_name = model_name.replace('_', '.create_')
        else:
            permission_name = '?'
            return 'Error'

        return user.has_perm(permission_name)

    def set_uploaded_files(self):
        '''
        Change the properties of the suggestion's primary instance where there is an entry for uploaded file(s)
        :return:
        '''

        if self.suggestupload_set.count() == 0:
            return

        i = self.primary.instance

        # Follow a 'suggestion chain' to the primary instance
        while isinstance(i, Suggest):
            i = i.primary.instance

        for f in self.suggestupload_set.all():
            name = os.path.split(f.upload.name)[-1]
            try:
                file_field = getattr(i, f.field_name)
                file_field.save(name, f.upload.file)
            except AttributeError, e: #  Happens using image insertion into Summernote
                logger.error(e.message)
                continue
            except IntegrityError, e:
                logger.error(e.message)
                continue


        # i.save()

    def _set(self, data=None, write=True):
        """
        
        :param data: 
        :return: Boolean, String, Exception or None
        """
        logger.debug('Loading data for %s' % self)
        ready = True
        changed = False

        if not data:
            data = self.data

        # Return if there are no pending suggestions
        m = re.search('_(\d+)_', data)

        if not m:
            logger.debug('No foreign keys in data')
            return True, changed, data

        else:

            # Follow chain of suggestions
            p = self.primary
            while p.model_name == 'suggest_suggest':
                p = p.instance.primary
            instance = p.instance

            if not hasattr(instance, '_meta'):
                error = {'Error': 'Problem following the primary instance'}
                return False, False, json.dumps(error)
            model = instance._meta.model

            _d = self.data_jsonify()
            for k, v in _d.items():
                try:
                    t = get_field_type(model, k)
                except FieldDoesNotExist:
                    logger.debug('Field %s does not exist')
                    continue
                except KeyError:
                    logger.debug('Field %s does not exist')
                    continue

                if t not in ['ForeignKey', 'ManyToManyField']:  # Add other eligible FieldTypes here
                    continue

                related = self.follow(k)
                if not related:
                    continue

                # Leave it alone if it's an unfilled suggestion
                if isinstance(related, Suggest) and (related.state != 'CM' or related.state != 'A'):
                    ready = False
                    continue

                if t == 'ForeignKey' and str(related.pk) != str(v):
                    _d[k] = str(related.pk)
                    changed = True

                # UNTESTED CODE!!!
                elif t == 'ManyToManyField':
                    for index, i in enumerate(related):

                        # A Suggest object has been approved: update the SUggestion pk to the Object's pk
                        if not isinstance(i, Suggest):
                            if str(i.pk) != str(_d[k][index]):
                                print 'Updated: %s -> %s' % (_d[k][index], i.pk)
                                _d[k][index] = i.pk
                                changed = True
                            continue

                        if isinstance(i, Suggest) and (i.state != 'CM' or i.state != 'A'):
                            ready = False
                            continue
                        pk = i.primary.instance.pk

                        if pk is not None:
                            _d[k][index] = pk
                            changed = True
                        else:
                            ready = False

        try:
            dump = json.dumps(_d)
        except TypeError:
            raise

        if write is True:
            self.data = dump
            self.save()

        return ready, changed, dump

    @property
    def _url(self):

        r = {
            'ready': False,
            'url': '',
            'exception': None
        }

        m = re.search('_(\w+)_', self.url)

        if not m:
            r['ready'], r['url'], r['exception'] = True, self.url, None
            return r

        rel_pk = int(m.groups()[0])
        try:
            related = Suggest.objects.get(pk=rel_pk)
        except Suggest.DoesNotExist:
            r['ready'], r['url'], r['exception'] = False, '', 'Parent suggestion removed'
            return r

        if related.primary.model_pk:
            self.url = re.sub('_(\w+)_', str(related.primary.model_pk), self.url)
            self.save()
            r['ready'], r['url'], r['exception'] = True, self.url, None
        else:
            r['ready'], r['url'], r['exception'] = False, None, 'Parent suggestion is not applied yet'

        return r

    @property
    def prepare(self):
        '''
        Return the data with any values dependent on another suggestion appropriately replaced
        :return: Boolean, Exception
        '''

        ready, changed, dump = self._set(write=True)

        if not ready:
            return {'ready': False, 'exception': 'Not ready'}
        return self._url

    @property
    def primary(self):
        """
        Returns an AffectedInstance object which is the 'primary' object being affected
        """
        try:
            return self.affectedinstance_set.get(primary=True)
        except:
            raise

    def highlight_changes(self):

        def is_same(value_a, value_b):

            try:
                return int(value_a) == int(value_b)
            except:
                pass

            try:
                return '{}'.format(value_a) == '{}'.format(value_b)
            except:
                pass

            try:
                return value_a == value_b
            except:
                pass

            return False

        changes = []
        # Changes in format (name, old, new)

        primary = self.primary
        if not primary:
            return None

        if not self.data:
            return None

        try:
            instance = primary.instance
            model = getattr(instance, '__class__')
        except:
            model = primary.retrieve_model()
            if not model:
                return (('Error', 'No primary model', 'No primary model', False))
            instance = model()

        # Compare the instance attributes to the model's current attributes
        # for attr, val in json.loads(self.data).items():

        data_ready, _data, data_exception = self._data

        # Special exemption for sets
        # Set data example: {"projectplace_set": [{"project": 24536, "place": 5}, {"project": 24536, "place": 12}]}


        for attr, val in json.loads(str(self.data)).items():

            try:
                field_type = get_field_type(instance, attr)
            except models.FieldDoesNotExist:
                # changes.append((attr, 'No attribute!', val, False))
                continue

            if val is None:
                if self.action != 'CM':
                    current_value = getattr(instance, attr)
                    changes.append((attr, current_value, 'X', is_same(val, current_value)))
                continue

            if field_type == 'ForeignKey':

                if val.isdigit():
                    try:
                        rel = model._meta.get_field(attr).rel.to
                        val = rel.objects.get(pk__in=[val, '{}'.format(val)])
                    except Exception, e:
                        val = e.message

                elif val.startswith('_') and val[1:-1].isdigit():
                    val = '(New item)'
                else:
                    try:
                        rel = model._meta.get_field(attr).rel.to
                        val = rel.objects.get(pk__in=[val, '{}'.format(val)])
                    except Exception, e:
                        val = e.message

            elif field_type == 'DateField':
                val = dateutil.parser.parse(val).date()

            if field_type == 'ManyToManyField':
                # List from an m2m field. Compare with current objects: pk or 'name' fields can be used

                if self.primary.model_pk:
                    try:
                        current_values = getattr(instance, attr).all()
                    except:
                        current_values = []
                else:
                    current_values = val

                rel = model._meta.get_field(attr).rel.to
                q = Q(pk__in=[int(i) for i in val if i.isdigit()])
                if hasattr(model(), 'name'):
                    q = q | Q(name__in=[i for i in val if not i.isdigit()])
                vals = rel.objects.filter(q)

                # if this has not been created yet everything should be green - so everything should be
                # in vals

                # for removed in set(current_values) - set(vals):
                #     if self.action == 'CM' and self.state == 'W':
                #         pass
                #         # If this is "create model" don't highlight the change as a removal
                #         # changes.append((attr, removed, removed, True))
                #     else:
                #         changes.append((attr, removed, None, False))


                for added in set(vals) - set(current_values):
                    changes.append((attr, '', added, False))
                for unchanged in set(vals).intersection(set(current_values)):
                    changes.append((attr, unchanged, unchanged, True))

                continue

            if self.action == 'CM' and self.state == 'W':
                changes.append((attr, '', val, False))

            else:
                try:
                    current_value = getattr(instance, attr)
                    changes.append((attr, current_value, val, is_same(val, current_value)))
                except Exception, e:
                    changes.append((attr, e.message, val, False))

        # Include suggested file fields
        for u in self.suggestupload_set.all():
            changes.append((u.field_name, '-', mark_safe('<a href="%s">%s</a>' % (u.upload.url, u.upload.name)), '-'))

        return changes

    @property
    def changes(self):
        '''
        Shortcuts to highlight_changes
        If no primary model is specified, instead return just the data
        :return:
        '''

        def _suggestions(l):
            ret = []
            for pk in l:
                s = re.match('_(\w+)_', unicode(pk))
                print s
                if s:
                    ret.append(s.groups()[0])
            return Suggest.objects.filter(pk__in = ret)

        def wrap_class(text, css_class):

            if isinstance(text, list):
                if len(text) == 0:
                    return ''
                text = u', '.join([u'{}'.format(i) for i in text])

            return mark_safe(u'<span class="{}">{}</span>'.format(css_class, text))
        try:
            i = self.primary.instance

            while isinstance(i, Suggest):
                i = i.primary.instance

        except:
            return {}
        returns = {}
        ready, changed, suggestion_data = self._set(write=False)
        suggestion_data = json.loads(suggestion_data)

        # TODO: More elegant return for models which do not exist
        if self.state == 'A' and self.action == 'DM':
            return returns
        if self.primary.instance == 'Removed':
            return returns
        # Call _set to prepare data
        if not hasattr(self.primary.instance, 'pk'):
            return returns

        if i.pk:

            for key, value_suggested in suggestion_data.items():

                if not hasattr(i, key):
                    continue

                value_current = getattr(i, key)

                if get_field_type(i, key) == 'ManyToManyField':
                    # Get a list of primary key values related
                    pks = getattr(i, key).all().values_list('pk', flat=True)
                    value_current = set([str(_i) for _i in pks if not re.match('_(\w+)_', unicode(_i))])

                    # Get a set of suggested, updated, primary keys
                    value_new = set([v for v in value_suggested if not re.match('_(\w+)_', unicode(v))])

                    f = i._meta.get_field(key).rel.to

                    keep = value_current & value_new
                    drop = value_current - value_new
                    add = value_new - value_current

                    current_objects = [u'%s' % (o) for o in f.objects.filter(pk__in=value_current)]
                    drop_objects = [u' - %s' % (o) for o in f.objects.filter(pk__in=drop)]
                    add_objects = [u' + %s' % (o) for o in f.objects.filter(pk__in=add)]
                    keep_objects = [u'%s' % (o) for o in f.objects.filter(pk__in=keep)]

                    # Include "added" objects which are new
                    add_objects.extend([u' + %s' % (o) for o in _suggestions(value_suggested)])
                    r = ';'.join([wrap_class(keep_objects or u"None unchanged", u'unchanged'),
                                  wrap_class(add_objects, u'added'), wrap_class(drop_objects, u'removed')])
                    returns[key] = r

                elif get_field_type(i, key) == 'ForeignKey':

                    value_suggested = self.follow(key)
                    if value_current == value_suggested and value_suggested is not None:
                        returns[key] = wrap_class(value_current, u'unchanged')
                    elif value_suggested is None:
                            returns[key] = None
                    else:
                        returns[key] = mark_safe(u"{} {}").format(wrap_class(value_current, u'removed'),
                                                                 wrap_class(value_suggested, u'added'))

                else:
                    if value_current == value_suggested and value_suggested is not None:
                        returns[key] = wrap_class(value_current, u'unchanged')
                    elif value_suggested is None:
                        returns[key] = None
                    # Try coercing to the same value
                    elif '{}'.format(value_suggested) == '{}'.format(value_current):
                        returns[key] = wrap_class(value_current, u'unchanged')
                    else:
                        returns[key] = mark_safe(u"{} {}").format(wrap_class(value_current or '', u'removed'),
                                                                 wrap_class(value_suggested, u'added'))

        else:
            for key, value_suggested in suggestion_data.items():
                if value_suggested is None:
                    returns[key] = None
                else:
                    try:
                        returns[key] = wrap_class(self.follow(key) or value_suggested, u'unchanged')
                    except KeyError: #  This happens eg on -file-clear fields
                        returns[key] = wrap_class(value_suggested, u'unchanged')

        return returns

    def simple_fields(self, fmt='flat'):
        """
        Return value of all fields which are not relationships
        """
        if fmt in ['list', 'flat']:
            returns = []
        elif fmt == 'dict':
            returns = {}
        try:
            obj = self.primary.instance
        except AffectedInstance.DoesNotExist:
            # warnings.warn('There is no primary instance for suggestion %s'%self.pk)
            return returns

        field_names = [i.name for i in obj._meta.fields]
        m2m_names = [i.name for i in obj._meta.many_to_many]

        for key, value in self.data_jsonify().items():
            if key not in field_names and key not in m2m_names:
                continue
            field_type = get_field_type(obj, key)
            if field_type in ['ForeignKey', 'ManyToManyField']:
                continue
            if fmt == 'list':
                returns.append(value)
            elif fmt == 'dict':
                returns[key] = value
            elif fmt == 'flat':
                k = value
                if isinstance(k, list):
                    for _k in k:
                        returns.append((key, _k))
                else:
                    returns.append((key, k))
        return returns

    def references(self, fmt='flat'):
        """
        Return all foreign keys and their current status
        :return:

        Options for 'fmt' are 'flat', 'dict' or 'list'.
        Default is 'flat which returns a list of key, instance pairs.

        """
        if fmt in ['list', 'flat']:
            returns = []
        elif fmt == 'dict':
            returns = {}

        obj = self.primary.instance
        while isinstance(obj, Suggest):
            if obj.state in ('D', 'R'):
                return []
            obj = obj.primary.instance

        # TODO: Better error handling

        if isinstance(obj, basestring):
            if self.state in ('D', 'R'):
                return []
            assert (self.state == "A" and self.action == 'DM')
            return []

        if not hasattr(obj, '_meta'):
            raise TypeError('No _meta for this object - ensure obj is a "model" instance')

        field_names = [i.name for i in obj._meta.fields]
        m2m_names = [i.name for i in obj._meta.many_to_many]

        for key in self.data_jsonify().keys():
            if key not in field_names and key not in m2m_names:
                continue
            field_type = get_field_type(obj, key)
            if field_type not in ['ForeignKey', 'ManyToManyField']:
                continue
            if fmt == 'list':
                returns.append(self.follow(key))
            elif fmt == 'dict':
                returns[key] = self.follow(key)
            elif fmt == 'flat':
                k = self.follow(key)
                if isinstance(k, list):
                    for _k in k:
                        returns.append((key, _k))
                else:
                    returns.append((key, k))
            else:
                raise TypeError('Invalid option for "fmt": try one of list, flat or dict')
        return returns

    def parent(self):

        parent = Suggest.objects.filter(
                pk__in=[int(i) for i in
                        self.affectedinstance_set.filter(model_name='suggest_suggest').values_list('model_pk',
                                                                                                   flat=True)])

        return parent

    def children(self):
        return Suggest.objects.filter(
                pk__in=[int(i) for i in
                        AffectedInstance.objects.filter(model_name='suggest_suggest', model_pk=self.pk).values_list(
                                'suggestion_id', flat=True)])

    @property
    def related_changes(self):
        """
        Inspect the "AffectedInstance(s)" of this suggestion and return
        suggestions related to those affected instances ('chaining' suggestions)
        """

        # Any parent instance
        return {
            'parent':
                self.parent(),
            'children':
                self.children()
        }

    @property
    def email_obfs(self):
        '''
        Obfuscated email - cut off the middle digits to hide identity
        :return:
        '''

        begin = self.email[0:3]
        end = self.email.split('@')[-1]
        middle = len(self.email) - len(begin) - len(end)

        return self.email[0:3] + '*' * middle + '@' + end

    def data_jsonify(self, include_files=False):
        """
        Load the 'data' of this suggestion as a dictionary
        :return:
        Skip files if you intend to reserialize
        """
        if not self.data:
            return {}
        try:
            d = json.loads(self.data)
        except:
            raise TypeError("Error! Data was {}".format(self.data))
        if include_files:
            for f in self.suggestupload_set.all():
                d[f.field_name] = f.upload
        return d

    def parseurl(self):

        url = u'{}'.format(self.url)
        # Dependent URLS (for example, updates requested to a model not yet create)
        # use _0001_ to identify the primary key of an AffectedInstance object

        search = re.compile('(?:_)([0-9]*)(?:_)')
        s = re.search(search, url)

        if s:
            affected_instance_pk = int(s.groups()[0])
            affected_instance = AffectedInstance.objects.get(pk=affected_instance_pk)
            model = _get_model(affected_instance.model_name)
            instance = model.objects.get(pk=affected_instance.model_pk)

            logger.info('_[0-9]+_', url, instance.pk)
            url = re.sub("_\d+_", str(instance.pk), url)
            logger.info(url)

        if not url.endswith('/'):
            url += '/'

        return url
