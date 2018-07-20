import json
from nhdb.models import Organization
from rest_framework import serializers
from models import Publication, Pubtype, Version, Author, Tag

__author__ = "josh"


class OrganizationAllowsNames(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(pk=data)
        except (TypeError, ValueError):
            try:
                return Organization.objects.get(name=data).pk
            except Organization.DoesNotExist:
                name = data.replace("__new__", "")
                o = Organization(name=name, orgtype_id="None")
                o.save()
                return o.pk

    def __init__(self, **kwargs):
        super(OrganizationAllowsNames, self).__init__(**kwargs)


class AuthorAllowsNames(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):

        if isinstance(data, basestring):

            # Check that a "suggestion" hasn't been accidentally passed thru
            assert not (data.startswith("_") and data.endswith("_"))

            if data.isdigit():
                return self.get_queryset().get(pk=data)
            else:
                name = data.replace("__new__", "")
                return Author.objects.get_or_create(name=name)[0].pk

        elif isinstance(data, int):
            return self.get_queryset().get(pk=data)

    def __init__(self, **kwargs):
        super(AuthorAllowsNames, self).__init__(**kwargs)


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = "__all__"

    organization = OrganizationAllowsNames(
        many=True, queryset=Organization.objects.all(), allow_null=True, required=False
    )
    author = AuthorAllowsNames(
        many=True, queryset=Author.objects.all(), allow_null=True, required=False
    )


class PubtypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pubtype
        fields = "__all__"


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = "__all__"

    def create(self, validated_data):
        v = Version.objects.create(**validated_data)
        return v


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"
