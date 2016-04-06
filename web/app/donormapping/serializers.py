from donormapping.models import FundingOffer, FundingOfferDocument
from rest_framework import serializers


class FundingOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingOffer


class FundingOfferDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingOfferDocument
