from donormapping.models import FundingOffer, FundingOfferDocument
from rest_framework import serializers


class FundingOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingOffer
        fields = '__all__'


class FundingOfferDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingOfferDocument
        fields = '__all__'