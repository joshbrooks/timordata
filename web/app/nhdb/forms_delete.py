from suggest.forms import SuggestionDeleteForm as s
from nhdb import models as m


class ProjectDeleteForm(s):
    class Meta:
        fields = ()
        model = m.Project

    def __init__(self, project, *args, **kwargs):
        super(ProjectDeleteForm, self).__init__(instance=project, *args, **kwargs)
        self.instance = project


class OrganizationDeleteForm(s):
    class Meta:
        fields = ()
        model = m.Organization

    def __init__(self, organization, *args, **kwargs):
        super(OrganizationDeleteForm, self).__init__(instance=organization, *args, **kwargs)
        self.instance = organization


class ProjectImageDeleteForm(s):
    class Meta:
        model = m.ProjectImage
        fields = []

    def __init__(self, projectimage=None, *args, **kwargs):
        super(ProjectImageDeleteForm, self).__init__(instance=projectimage, *args, **kwargs)
        self.instance = projectimage


class OrganizationPlaceDeleteForm(s):
    '''
    Renders a buttonform to suggest deleting an organizationplace
    '''

    class Meta:
        fields = ()
        model = m.OrganizationPlace

    def __init__(self, organizationplace, *args, **kwargs):
        super(OrganizationPlaceDeleteForm, self).__init__(instance=organizationplace, *args, **kwargs)
        self.instance = organizationplace


class ProjectplaceDeleteForm(s):
    '''
    Renders a buttonform to suggest deleting an projectplace
    '''

    class Meta:
        fields = ()
        model = m.ProjectPlace

    def __init__(self, projectplace, *args, **kwargs):
        super(ProjectplaceDeleteForm, self).__init__(instance=projectplace, *args, **kwargs)
        self.instance = projectplace


class ProjectPersonDeleteForm(s):

    class Meta:
        model = m.ProjectPerson
        fields = ()

    def __init__(self, projectperson, *args, **kwargs):
        super(ProjectPersonDeleteForm, self).__init__(instance=projectperson, *args, **kwargs)
        self.instance = projectperson


class ProjectOrganizationDeleteForm(s):

    class Meta:
        model = m.ProjectOrganization
        fields = ()

    def __init__(self, projectorganization, *args, **kwargs):
        super(ProjectOrganizationDeleteForm, self).__init__(instance=projectorganization, *args, **kwargs)
        self.instance = projectorganization