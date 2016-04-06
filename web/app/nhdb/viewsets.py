from rest_framework import viewsets
from nhdb.serializers import *
from nhdb.models import *
from nhdb.views_helpers import projects_page
from rest_framework.response import Response
__all__ = [
    'ProjectViewSet',
    'ProjectSearchViewSet',
    'OrganizationViewSet','ProjectPersonViewSet',
    'Project_ProjectPersonViewSet',
    'ProjectOrganizationViewSet',
    'Project_ProjectPlaceViewSet'
    ]

class ProjectViewSet(viewsets.ModelViewSet):

    serializer_class = ProjectSerializer
    queryset = Project.objects.all()


class OrganizationViewSet(viewsets.ModelViewSet):

    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()


class ProjectSearchViewSet(viewsets.ViewSet):
    """
    
    """
    
    #queryset = Project.objects.all()
    def list(self, request):
        
        paginator, page = projects_page(rq = request)
        serializer = PaginatedProjectSearch(paginator.page(page),context={'request': request})
        return Response(serializer.data)

class ProjectPersonViewSet(viewsets.ModelViewSet):
    
    serializer_class=ProjectPersonSerializer
    queryset = ProjectPerson.objects.all()
    
class Project_ProjectPersonViewSet(viewsets.ModelViewSet):
    
    serializer_class=Project_ProjectPersonSerializer
    queryset = Project.objects.all()
    
class Project_ProjectPlaceViewSet(viewsets.ModelViewSet):
    
    serializer_class=Project_ProjectPlaceSerializer
    queryset = Project.objects.all()

class ProjectOrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectOrganizationSerializer
    queryset = ProjectOrganization.objects.all()
