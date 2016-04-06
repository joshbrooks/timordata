__author__ = 'josh'

from settings import LANGUAGES_FIX_ID
from crispy_forms.bootstrap import TabHolder, Tab
from crispy_forms.layout import Layout, Submit, HTML, Field, Div, Fieldset, ButtonHolder
from django.utils.translation import ugettext_lazy as _


def render_field(fieldname='test'):
    return HTML("""
    <div id="div_id_{0}" class="form-group">
        <label for="id_{0}" class="sr-only">
        {1}
        </label>
        <input class="textinput textInput form-control" id="id_{0}" maxlength="64" name="{0}" placeholder="{1}" type="text">
    </div>""".format(fieldname, fieldname.capitalize()))


class TranslationTabs():
    """
    Render a set of CrispyForm Tab objects
    """
    def __init__(self, languages=LANGUAGES_FIX_ID, fieldnames=('name', 'description')):

        self.tabs = []
        for language in languages:
            fieldnames_with_language = [f+'_'+language[0] for f in fieldnames]
            fields = [Field(fieldname_with_language) for fieldname_with_language in fieldnames_with_language]
            # fields = [render_field(fieldname_with_language) for fieldname_with_language in fieldnames_with_language]
            self.tabs.append(Tab(_(language[1]), *fields))

    @property
    def tabholder(self):
        return TabHolder(*self.tabs)
