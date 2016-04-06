
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'belun.settings'
import django
django.setup()

from crispy_forms.utils import render_crispy_form
from django.db.models.base import ModelBase
from django.forms.models import ModelFormMetaclass
import logging, sys
logger = logging.getLogger('nhdb.tests')
logger.setLevel(logging.ERROR)
logger.addHandler(logging.StreamHandler(sys.stderr))


def recommend_form_class(c, model):

    fields = [i.name for i in model._meta.fields if i.name != 'id']
    m2m = [i.name for i in model._meta.many_to_many]


    return """
class {0}Form(SuggestionForm):
    '''
    Auto generated form class - modify if ncecessary!
    '''
    class Meta:
        model = {0}
        exclude = []
        # fields = ()

    def __init__(self, {1}=None, *args, **kwargs):
        super({0}Form, self).__init__(_instance={1}, *args, **kwargs)

    @property
    def helper(self):
        helper = self.get_helper()
        helper.layout.extend({2})
        helper.layout.extend({3})
        return helper

""".format(c, c.lower(), fields, m2m)


def form_present(my_models, my_forms):

    def writeform(outfile, rendered, form_class, model, prefix='', instance=None):
        outfile.write(recommend_form_class(model_name, model))
        try:
            set = form_class.helper
        except:
            logger.warning('Helper failure for form class %s','%sForm'%(model_name))

        try:
            rendered.write('<h4>%s</h4>'%model_name)
            rendered.write('<div class="container"><div class="row"><div class="col col-lg-6"><h4>%s%sForm</h4>'%(prefix, model_name))
            if instance:
                r = render_crispy_form(form_class(instance))
            else:
                r = render_crispy_form(form_class())
            rendered.write(r.encode('utf-8'))
            rendered.write('</div></div></div>')

        except Exception, e:
            logger.error('Rendering error: %s \n model_name: %s \n form_class: %s', e, model_name, form_class)

    def writedeleteform(outfile, rendered, form_class, model, instance):
        return writeform(outfile, rendered, form_class, model, prefix='Delete', instance = instance)

    with open('/tmp/forms.py', 'w') as outfile:
        with open('/tmp/auto_generated_forms.html', 'w') as rendered:

            rendered.write('''
            <html><head>
                <script src="/webapps/project/static/jquery.js"></script>
                <script src="/webapps/project/static/bootstrap/js/bootstrap.min.js"></script>
                <link href="/webapps/project/static//bootstrap/css/bootstrap.min.css" rel="stylesheet">
                </head>
                <body>
                ''')

            outfile.write('from suggest.forms import SuggestionForm')
            outfile.write('from nhdb.models import *')

            form_list = [i for i in dir(my_forms) if isinstance(getattr(my_forms, i), ModelFormMetaclass)]
            print form_list
            model_list = [i for i in dir(my_models) if isinstance(getattr(my_models, i), ModelBase)]
            print model_list

            for model_name in model_list:
                form_class = None
                for i in form_list:
                    if '{}form'.format(model_name).lower() != i.lower():
                        continue
                    else:
                        form_class = getattr(my_forms, i)
                        model = getattr(my_models, model_name)
                        writeform(outfile, rendered, form_class, model)
                        break

                if not form_class:
                    logger.warning('No class {}Form found', model_name)

                form_class = None

                for i in form_list:
                    if '{}deleteform'.format(model_name).lower() != i.lower():
                        continue
                    else:
                        form_class = getattr(my_forms, i)
                        model = getattr(my_models, model_name)

                        try:
                            instance = form_class.Meta.model.objects.first()

                            writedeleteform(outfile, rendered, form_class, model, instance)
                        except:
                            raise
                        break

                if not form_class:
                    logger.warning('No class {}DeleteForm found', model_name)

            rendered.write('</body></html>')

if __name__ == '__main__':

    from nhdb import models as my_models
    from nhdb import forms as my_forms
    form_present(my_models, my_forms)