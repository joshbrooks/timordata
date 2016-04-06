from suggest.forms import SuggestionDeleteForm as S
from library import models


class PublicationDeleteForm(S):
    class Meta:
        model = models.Publication
        fields = []

    def __init__(self, publication, *args, **kwargs):
        super(PublicationDeleteForm, self).__init__(publication, *args, **kwargs)
        self.instance = publication


class VersionDeleteForm(S):
    class Meta:
        model = models.Version
        fields = []

    def __init__(self, version=None, *args, **kwargs):

        super(VersionDeleteForm, self).__init__(version, *args, **kwargs)
        self.instance = version
