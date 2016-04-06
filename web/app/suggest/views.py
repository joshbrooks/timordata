import json
from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, DetailView
from django_tables2 import SingleTableView
from rest_framework.renderers import JSONRenderer
from suggest.models import Suggest, AffectedInstance, SuggestUpload
from suggest.serializers import SuggestSerializer
from suggest.tables import SuggestTable
from suggest.forms import SuggestionForm, SuggestDeleteForm, SuggestionDeleteForm
import logging, sys
logger = logging.getLogger('suggest.views')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stderr))


@login_required
@require_POST
def hide(request, model_name, model_pk, state='all'):
    '''
    Send me a POST request to toggle 'is_hidden' to TRUE so it won't show by default in the list of suggestions
    EG '/suggest/clear/nhdb_project/23407/all/' should delete all suggestions for project 23407

    status can be 'W', 'A', 'C', 'E' (Waiting, Approved, Cancelled, Error)

    :param model_name:
    :param model_pk:
    :return:
    '''

    l = Suggest.objects.filter(affectedinstance__model_name=model_name, affectedinstance__model_pk=model_pk)
    if state != 'all':
        l = l.filter(state=state)

    for i in l:
        i.is_hidden = True
        i.save()

    return redirect('/suggest/{}/{}/'.format(model_name, model_pk))


@login_required
@require_POST
def unhide(request, model_name, model_pk, state='all'):
    '''
    Show everything (reverse effects of hiding suggestions)
    :param model_name:
    :param model_pk:
    :return:
    '''
    l = Suggest.objects.filter(affectedinstance__model_name=model_name, affectedinstance__model_pk=model_pk)
    # if state != 'all':
    # list.filter(state = state)

    for i in l:
        i.is_hidden = False
        i.save()

    return redirect('/suggest/{}/{}/'.format(model_name, model_pk))


class SuggestList(SingleTableView):
    table_class = SuggestTable
    model = Suggest

    def get_context_data(self, **kwargs):

        queryset = Suggest.objects.all()
        context = super(SuggestList, self).get_context_data(**kwargs)

        context['filters'] = {
            'model_name': set(AffectedInstance.objects.all().values_list('model_name', flat=True)),
            'action': Suggest._meta.get_field('action').choices,
            'state' : Suggest._meta.get_field('state').choices,
            'user_name': set(Suggest.objects.all().values_list('user_name', flat=True)),
        }

        context['activefilters'] = {}

        for i in context['filters']:
            context['activefilters'][i] = self.request.GET.getlist(i)

        context['return_url'] = self.request.GET.get('return_url')
        model_name = self.kwargs.get('model_name') or self.request.GET.get('model_name')
        model_pk = self.kwargs.get('model_pk') or self.request.GET.get('model_pk')
        context['model_name'] = model_name
        context['model_pk'] = model_pk
        context['email'] = self.request.GET.get('email')

        # If there is a model_name and model_pk
        if model_name and model_pk:
            try:
                a, m = model_name.split('_') # "eg nhdb_project" -> ['nhdb', 'project']
            except ValueError:
                raise ValueError, "Expected an underscored app_project name eg nhdb_project -> ['nhdb', 'project']. Got %s"%model_name
            context['model'] = apps.get_model(a, m)
            context['object'] = context['model'].objects.get(pk = model_pk)

            if not context['return_url']:
                try:
                    context['return_url'] = context['object'].get_absolute_url()
                except:
                    pass

        context['tabs'] = {'first':{'disabled':True}}

        return context

    def get_queryset(self):

        def _filter():
            _l = self.request.GET.getlist
            filters = {
                'affectedinstance__model_name__in': _l('model_name'),
                'affectedinstance__model_pk__in': _l('model_pk'),
                'state__in': _l('state'),
                'action__in': _l('action'),
                'user_name__in': _l('user_name'),
                'email': _l('email'),
                'is_hidden': False
            }
            for k, v in filters.items():
                if v is None or v == [] or v == [None]:
                    filters.pop(k)
            return filters

        def _extra(qs):
            """
            Also include suggestions where the "affected instance" model is a suggestion
            :param qs:
            :return:
            """
            queryset_extra = Suggest.objects.filter(
                affectedinstance__model_name='suggest_suggest',
                affectedinstance__model_pk__in=[str(i) for i in qs.values_list('pk', flat=True)]
            )
            if queryset_extra.count() == 0:
                return qs

            pk_list = list(qs.values_list('pk', flat = True))
            pk_list.extend(list(queryset_extra.values_list('pk', flat = True)))
            qs = Suggest.objects.filter(pk__in = pk_list)
            return qs

        queryset_with_extra = _extra(Suggest.objects.filter(**_filter()).distinct())

        return queryset_with_extra.order_by('-id')




class SuggestCreate(CreateView):
    model = Suggest
    form_class = SuggestionForm


def suggest(request, pk):
    context = {'suggest': Suggest.objects.get(pk=pk)}
    return render(request, 'suggest/suggest_detail.html', context)


def suggest_ajax(request, pk):
    try:
        suggest = Suggest.objects.get(pk=pk)
    except Suggest.DoesNotExist:
        return render(request, 'suggest/doesnotexist.html', {})
    try:
        permission_granted = suggest.perm(request.user)
    except:
        permission_granted = False
    context = {'suggest': suggest, 'permission_granted': permission_granted}
    return render(request, 'suggest/suggest_detail_ajax.html', context)


def suggestdelete(request, pk):
    """
    Return a modelform to delete the suggestion
    :param request:
    :param pk:
    :return:
    """
    context = {'form': SuggestionDeleteForm(instance = Suggest.objects.get(pk=pk))}
    return render(request, 'suggest/crispy_form.html', context)


@csrf_exempt
@require_POST
def suggestcreate(request):

    """
    Create a suggested change to information in the database
    This interfaces with the django-rest API to provide a way to "confirm" changes to database data
    (POST) Parameters:
        '_affected_instance',
        'has_many', multiple, name of another parameter to be treated as an array not a single item
        'data',
        'return_url', in conjunction with 'return_param' and 'return_param_passthrough', generates a URL for the
        next form ('chaining' forms like Create Project -> Create Person -> Create Link from Person to Project)
        'return_param'
        anything else gets folded into 'data' to allow a standard form to be used

        Information about submission treated separately:
        _name
        _email
        _comment

    :param request:
    :return:
    """

    def get_primary_affected_instance(r):
        """
        Convert a request parameter _affected_instance_primary to an AffectedInstance object
        EG "nhdb_project 32442" or "library_publication"
        :param r:
        :return:
        """

        i = r.POST.get('_affected_instance_primary', None)
        assert i, "There is no affected primary instance field on the submission - must have '_affected_instance_primary=nhdb project' or similar"

        assert '_' in i, 'Expected a string of the form "appname_modelname" but received {}'.format(i)

        if ' ' in i:
            model_name, model_pk = i.split(' ')
        else:
            model_name = i
            model_pk = None
        if model_pk == 'None':
            model_pk = None
        if isinstance(model_pk, basestring) and model_pk.startswith('_'):
            model_pk = None

        return AffectedInstance(model_name=model_name, model_pk=model_pk, primary=True)

    warnings = []
    s = Suggest()
    s.user_id = request.user.pk
    s.user_name = request.user.__unicode__()

    if request.POST.get('data'):
        data = json.loads(request.POST.get('data'))
    else:
        data = {}

    meta_fields = ['csrfmiddlewaretoken', '_affected_instance', 'has_many', 'Submit', 'data', 'return_url', 'return_param', 'return_param_passthrough', '_next', '_affected_instance_primary']

    meta_fields.extend(list(set(request.POST.getlist('has_many'))))

    for key, value in request.POST.items():

        if key.startswith('__') or key in meta_fields:
            continue

        elif key.startswith('_'):  # Values with an underscore are from the metadata to be stored in Suggest table
            try:
                setattr(s, key[1:], value)
                continue
            except KeyError:
                warnings.append('No property {} of suggestion'.format(key[1:]))
                raise TypeError(warnings)

        # Fix empty strings to null values
        if value == "" or value == 'None':
            value = None

        # Fix radio value of "on" or "off" to True or False
        if value == "on":
            value = True
        if value == "off":
            value = False

        # 'data' can be passed explicitly as JSON or passed as form values
        data[key] = value

    for _key in list(set(request.POST.getlist('has_many'))):
        if not data.get(_key):
            data[_key] = []
        for value in request.POST.getlist(_key):
            data[_key].append(value)
        if not data[_key]:
            data.pop(_key)

    #  "DELETE" requests need no additional data
    if s.method != 'DELETE':
        s.data = json.dumps(data)
    try:
        s.skip_signal=True
        s.save()
    except Exception, e:
        raise

    for field_name, file in request.FILES.items():
        SuggestUpload(suggestion=s, field_name=field_name, upload=file).save()

    if not request.POST.getlist('_affected_instance_primary'):
        raise AssertionError, 'Affected instance should be supplied'
        pass

    if warnings:
        return HttpResponse(content=json.dumps(warnings), content_type='application/json', status=400)

    serialized_data = SuggestSerializer(s).data
    return_url = request.POST.get('return_url')

    if return_url:
        get_params = {}
        for i in request.POST.getlist('return_param'):
            get_params[i] = '_%s_'%(s.id)
        for i in request.POST.getlist('return_param_passthrough'):
            name, value = i.split(' ')
            get_params[name] = value

        get_url = '&'.join(['{}={}'.format(i, get_params[i]) for i in get_params])
        serialized_data['success_url'] = return_url + '?' + get_url

    if '_next' in request.POST:
        serialized_data['success_url'] = request.POST.get('_next').replace('_suggestion_', str(s.id))

    affected = get_primary_affected_instance(request)

    m = affected._meta

    for field in m.get_fields():
        if field.__class__.__name__ in ['FileField', 'ImageField', 'TranslationFileField', 'TranslationImageField']:
            clear_file_field = field.name+'-clear'
            if clear_file_field in request.POST:
                data[clear_file_field] = True
                continue
            else:
                data[clear_file_field] = False
                try:
                    data.pop(field.name)
                except KeyError:
                    continue

    s.data = json.dumps(data)
    assert s.state == 'W'

    try:
        s.skip_signal=False
        s.save()
    except Exception, e:
        raise

    s.save()
    affected.suggestion = s
    affected.save()

    content = JSONRenderer().render(serialized_data)

    return HttpResponse(content=content, content_type='application/json', status=201)
