from rest_framework.response import Response

__author__ = "josh"

from django.conf.urls import url, include
from rest_framework import routers, serializers, viewsets
from suggest.models import Suggest
from suggest.serializers import SuggestSerializer


class SuggestionViewSet(viewsets.ModelViewSet):
    queryset = Suggest.objects.all()
    serializer_class = SuggestSerializer


router = routers.DefaultRouter()
router.register(r"suggest", SuggestionViewSet)

urlpatterns = [
    url(r"^", include(router.urls)),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
