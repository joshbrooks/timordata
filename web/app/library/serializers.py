import json
import os

from nhdb.models import Organization, PropertyTag
from rest_framework import serializers, fields
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
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


class TagSerializer(ForeignKeySerializer):

    class Meta:
        model = Tag
        fields = ('pk', 'name')


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
        fields = ('id', 'name', 'organization', 'pubtype', 'year', 'organization', 'author', 'sector', 'tag',
                  )

    organization = OrganizationSerializer(many=True, allow_null=True, required=False)
    author = AuthorSerializer(many=True, allow_null=True, required=False)
    sector = SectorSerializer(many=True, allow_null=True, required=False)
    tag = TagSerializer(many=True, allow_null=True, required=False)

    def update(self, instance, validated_data):
        instance.organization = validated_data.pop('organization')
        instance.author = validated_data.pop('author')
        instance.sector = validated_data.pop('sector')
        instance.tag = validated_data.pop('tag')
        super(PublicationSerializer, self).update(instance, validated_data)
        instance = self.Meta.model.objects.get(pk=instance.pk)
        return instance


def file_object_info(obj):
    try:
        return {
            'size': obj.size,
            'name': obj.name,
            'valid': True,
            'path': obj.path,
        }

    except ValueError as error:
        return None

    except (IOError, OSError) as error:
        return {
            'size': 0,
            'name': '',
            '_valid': False,
            'path': obj.path,
            '_exists': os.path.exists(obj.path),
            '_error': u'%s' % error
        }


class FileObjectField(serializers.Field):
    def to_representation(self, obj):
        return file_object_info(obj)


class TranslatedFileObjectField(serializers.Field):

    def to_representation(self, obj):
        instance = obj.instance
        d = {}
        for language in settings.LANGUAGES_FIX_ID:
            field_name = '%s_%s' % (self.field_name, language[0])
            field = getattr(instance, field_name)
            d[language[0]] = file_object_info(field)
        return d

    def to_internal_value(self, obj):
        raise NotImplementedError(obj)


class ModelTranslatedField(serializers.Field):

    def __init__(self):
        super(ModelTranslatedField, self).__init__()

    def to_representation(self, obj):
        parent = self.parent
        instance = self.parent.instance
        # raise AssertionError((self.parent.fields['title_tet'], dir(self.parent)))
        fields = self.parent.fields
        d = {}
        for language in settings.LANGUAGES_FIX_ID:
            field_name = '%s_%s' % (self.field_name, language[0])
            field = fields.get(field_name)
            d[language[0]] = field
        return d

    def to_internal_value(self, obj):
        raise NotImplementedError(obj)


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = ['id', 'title', 'upload', 'cover']

    upload = TranslatedFileObjectField()
    cover = TranslatedFileObjectField()

    title = ModelTranslatedField()
    #
    # def to_representation(self, instance):
    #     r = super(VersionSerializer, self).to_representation(instance)
    #     r['title'] = r['title'] or dict(('%s' % (language[0]), None) for language in settings.LANGUAGES_FIX_ID)
    #     return r

    def create(self, validated_data):
        v = Version.objects.create(**validated_data)
        return v


class PublicationVersionsSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        r = super(PublicationVersionsSerializer, self).to_representation(instance)
        r['description'] = r['description'] or dict(('%s' % (language[0]), None) for language in settings.LANGUAGES_FIX_ID)
        return r

    class Meta:
        model = Publication
        fields = ['id', 'versions', 'description']

    versions = VersionSerializer(many=True, allow_null=True, required=False)
    description = ModelTranslatedField()


class PubtypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pubtype
