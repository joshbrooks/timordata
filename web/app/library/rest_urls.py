__author__ = 'josh'

from django.conf.urls import url, include
from rest_framework import routers, serializers, viewsets
from models import *
from serializers import *


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer


class PubtypeViewSet(viewsets.ModelViewSet):
    queryset = Pubtype.objects.all()
    serializer_class = PubtypeSerializer


class VersionViewSet(viewsets.ModelViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

router = routers.DefaultRouter()
router.register(r'publication', PublicationViewSet)
router.register(r'pubtype', PubtypeViewSet)
router.register(r'version', VersionViewSet)
router.register(r'author', AuthorViewSet)
router.register(r'tag', TagViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
