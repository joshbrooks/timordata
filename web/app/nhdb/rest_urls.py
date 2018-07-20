from django.conf.urls import url, include
from django.contrib.auth.models import User
from rest_framework import filters
from rest_framework import routers, serializers, mixins, viewsets
from nhdb.models import (
    Project,
    ProjectPerson,
    ProjectOrganization,
    ProjectPlace,
    Organization,
    OrganizationPlace,
    Person,
    ProjectImage,
    PropertyTag,
    ProjectType,
    ExcelDownloadFeedback,
)
from nhdb.serializers import (
    ProjectSerializer,
    ProjectPersonSerializer,
    TestProjectSerializer,
    ProjectOrganizationSerializer,
    ProjectPlaceSerializer,
    OrganizationSerializer,
    PersonSerializer,
    OrganizationPlaceSerializer,
    ProjectProjectOrganizationSerializer,
    ProjectProjectPlaceSerializer,
    ProjectPropertiesSerializer,
    ProjectProjectPersonSerializer,
    OrganizationOrganizationPlaceSerializer,
    ProjectPropertiesSerializerByID,
    ProjectImageSerializer,
    PropertyTagSerializer,
    ProjectTypeSerializer,
    ExcelDownloadFeedbackSerializer,
)
from rest_framework.pagination import PageNumberPagination

# from django_filters.rest_framework import DjangoFilterBackend


class UpdateModelViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """

    pass


class NoDeleteModelViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, and `list()` actions.
    """

    pass


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("url", "username", "email", "is_staff")


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    # filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    ordering_fields = ("verified", "name")
    filter_fields = ("activity", "sector", "organization", "beneficiary")

    def get_queryset(self):
        queryset = Project.objects.all()
        queryset = queryset.prefetch_related(
            "beneficiary", "sector", "activity", "organization"
        )
        return queryset


class ProjectProjectPersonViewSet(viewsets.ModelViewSet):
    queryset = ProjectPerson.objects.all()
    serializer_class = ProjectPersonSerializer


class ProjectPlaceViewSet(viewsets.ModelViewSet):
    queryset = ProjectPlace.objects.all()
    serializer_class = ProjectPlaceSerializer


class OrganizationPlaceViewset(viewsets.ModelViewSet):
    queryset = OrganizationPlace.objects.all()
    serializer_class = OrganizationPlaceSerializer


class OrganizationOrganizationPlaceViewset(NoDeleteModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationOrganizationPlaceSerializer


class ProjectOrganizationViewSet(viewsets.ModelViewSet):
    queryset = ProjectOrganization.objects.all()
    serializer_class = ProjectOrganizationSerializer


class TestViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = TestProjectSerializer


class ProjectPropertiesViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectPropertiesSerializer


class ProjectPropertiesIDViewSet(UpdateModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectPropertiesSerializerByID


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class ProjectProjectOrganizationViewSet(NoDeleteModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectProjectOrganizationSerializer


class ProjectProjectPlaceViewset(NoDeleteModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectProjectPlaceSerializer


class ProjectProjectPersonViewset(NoDeleteModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectProjectPersonSerializer


class ProjectImageViewSet(viewsets.ModelViewSet):
    queryset = ProjectImage.objects.all()
    serializer_class = ProjectImageSerializer


class PropertyTagViewSet(viewsets.ModelViewSet):
    queryset = PropertyTag.objects.all()
    serializer_class = PropertyTagSerializer


class ProjectTypeViewSet(viewsets.ModelViewSet):
    queryset = ProjectType.objects.all()
    serializer_class = ProjectTypeSerializer


class ExcelDownloadFeedbackViewSet(viewsets.ModelViewSet):
    queryset = ExcelDownloadFeedback.objects.all()
    serializer_class = ExcelDownloadFeedbackSerializer


router = routers.DefaultRouter()
router.register(r"user", UserViewSet, "user")

router.register(r"project", ProjectViewSet, base_name="projects")
router.register(r"projectperson", ProjectProjectPersonViewSet)
router.register(r"projectplace", ProjectPlaceViewSet)
router.register(r"propertytag", PropertyTagViewSet)
router.register(
    r"projectorganization", ProjectOrganizationViewSet, base_name="projectorganization"
)
router.register(
    r"projectproperties", ProjectPropertiesViewSet, base_name="projectproperties"
)
router.register(
    r"projectpropertiesbyid",
    ProjectPropertiesIDViewSet,
    base_name="projectproperties_id",
)
router.register(r"projectimage", ProjectImageViewSet, base_name="projectimage")
router.register(r"projecttype", ProjectTypeViewSet, base_name="projecttype")
router.register(r"person", PersonViewSet, base_name="person")
router.register(r"exceldownloadfeedback", ExcelDownloadFeedbackViewSet)

router.register(
    r"projectprojectorganization",
    ProjectProjectOrganizationViewSet,
    base_name="projectprojectorganization",
)
router.register(
    r"projectprojectplace", ProjectProjectPlaceViewset, base_name="projectprojectplace"
)
router.register(
    r"projectprojectperson",
    ProjectProjectPersonViewset,
    base_name="projectprojectperson",
)
router.register(r"organization", OrganizationViewSet, base_name="organization")
router.register(
    r"organizationplace", OrganizationPlaceViewset, base_name="organizationplace"
)
router.register(
    r"organizationorganizationplace",
    OrganizationOrganizationPlaceViewset,
    base_name="organizationorganizationplace",
)

urlpatterns = [
    url(r"^", include(router.urls, namespace="rest")),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
