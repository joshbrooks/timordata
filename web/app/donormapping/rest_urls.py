from django.conf.urls import url, include
from rest_framework import routers, serializers, viewsets
from models import *
from serializers import *


class FundingOfferViewSet(viewsets.ModelViewSet):
    queryset = FundingOffer.objects.all()
    serializer_class = FundingOfferSerializer


class FundingOfferDocumentViewSet(viewsets.ModelViewSet):
    queryset = FundingOfferDocument.objects.all()
    serializer_class = FundingOfferDocumentSerializer


router = routers.DefaultRouter()
router.register(r'fundingoffer', FundingOfferViewSet)
router.register(r'fundingofferdocument', FundingOfferDocumentViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
