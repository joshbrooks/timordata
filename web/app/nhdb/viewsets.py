from rest_framework import viewsets
from nhdb.serializers import *
from nhdb.models import *

__all__ = [
    "ProjectViewSet",
    "ProjectSearchViewSet",
    "OrganizationViewSet",
    "ProjectPersonViewSet",
    "Project_ProjectPersonViewSet",
    "ProjectOrganizationViewSet",
    "Project_ProjectPlaceViewSet",
]


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        queryset = Project.objects.all()
        queryset = queryset.prefetch_related("activity")
        return queryset


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()


class ProjectPersonViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectPersonSerializer
    queryset = ProjectPerson.objects.all()


class Project_ProjectPersonViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectProjectPersonSerializer
    queryset = Project.objects.all()


class ProjectOrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectOrganizationSerializer
    queryset = ProjectOrganization.objects.all()
