import json
from nhdb.models import Organization, PropertyTag
from rest_framework import serializers, fields
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.serializers import get_validation_error_detail
from models import Publication, Pubtype, Version, Author, Tag

__author__ = 'josh'


class ForeignKeySerializer(serializers.ModelSerializer):
    """
    Gives / takes a dict of "id" and "representation"
    """

    def to_representation(self, instance):
        if not instance.pk:
            return {'pk': None}

        fields = self.Meta.fields
        if 'pk' not in self.Meta.fields:
            fields += 'pk'

        return {field_name: getattr(instance, field_name) for field_name in fields}

    def get_value(self, data):
        """ Use the 'pk' attribute to get the instance """
        value = super(ForeignKeySerializer, self).get_value(data)
        if type(value) == dict and (value['pk'] is None or value['pk'] == ''):
            return None
        return value

    def to_internal_value(self, data):
        try:
            return self.Meta.model.objects.get(pk=data['pk'])
        except self.Meta.model.DoesNotExist:
            raise ValidationError('pk "{}" does not exist'.format(data['pk']))

    def validate_empty_values(self, data):
        if type(data) == dict and data['pk'] is None:
            if not self.allow_null:
                self.fail('null')
            else:
                return (True, None)
        return super(ForeignKeySerializer, self).validate_empty_values(data)

    def get_attribute(self, transaction):
        representation = super(ForeignKeySerializer, self).get_attribute(transaction)
        if representation is not None:
            return representation
        else:
            return self.Meta.model()


class OrganizationAllowsNames(serializers.PrimaryKeyRelatedField):

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(pk=data)
        except (TypeError, ValueError):
            try:
                return Organization.objects.get(name=data).pk
            except Organization.DoesNotExist:
                name = data.replace('__new__','')
                o = Organization(name=name, orgtype_id='None')
                o.save()
                return o.pk

    def __init__(self, **kwargs):
        super(OrganizationAllowsNames, self).__init__(**kwargs)


class OrganizationSerializer(ForeignKeySerializer):

    class Meta:
        model = Organization
        fields = ('pk', 'name')


class SectorSerializer(ForeignKeySerializer):

    class Meta:
        model = PropertyTag
        fields = ('pk', 'name')


class AuthorSerializer(ForeignKeySerializer):

    class Meta:
        model = Author
        fields = ('pk', 'name', 'displayname')


class AuthorAllowsNames(serializers.PrimaryKeyRelatedField):

    def to_internal_value(self, data):

        if isinstance(data, basestring):

            # Check that a "suggestion" hasn't been accidentally passed thru
            assert not (data.startswith('_') and data.endswith('_'))

            if data.isdigit():
                return self.get_queryset().get(pk=data)
            else:
                name = data.replace('__new__','')
                return Author.objects.get_or_create(name=name)[0].pk

        elif isinstance(data, int):
            return self.get_queryset().get(pk=data)

    def __init__(self, **kwargs):
        super(AuthorAllowsNames, self).__init__(**kwargs)


class PublicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publication
        fields = ('name', 'organization', 'pubtype', 'year', 'organization', 'author')

    organization = OrganizationSerializer(many=True, allow_null=True, required=False)
    author = AuthorSerializer(many=True, allow_null=True, required=False)

    def update(self, instance, validated_data):
        instance.organization = validated_data.pop('organization')
        instance.author = validated_data.pop('author')
        super(PublicationSerializer, self).update(instance, validated_data)
        instance = self.Meta.model.objects.get(pk=instance.pk)
        return instance


class PubtypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pubtype


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version

    def create(self, validated_data):
        v = Version.objects.create(**validated_data)
        return v


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag