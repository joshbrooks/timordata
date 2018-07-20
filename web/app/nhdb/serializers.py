from django.contrib.gis.geos import Point
from rest_framework import serializers
from nhdb.models import (
    Organization,
    Project,
    ProjectOrganization,
    ProjectPerson,
    Person,
    ProjectPlace,
    PropertyTag,
    OrganizationPlace,
    ProjectImage,
    ProjectType,
    ExcelDownloadFeedback,
)
from geo.models import AdminArea, Suco


class SimpleProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = (
            "activity",
            "beneficiary",
            "sector",
            "place",
            "person",
            "organization",
        )


class OrganizationSerializer(serializers.ModelSerializer):
    # place = serializers.RelatedField(many=True)

    class Meta:
        model = Organization
        fields = ("name", "id")


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            "name",
            "description",
            "startdate",
            "enddate",
            "verified",
            "status",
            "organization",
            "beneficiary",
            "sector",
            "activity",
        )


class SimplePersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person


class PersonIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ("id", "name")


class ProjectOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOrganization


class ProjectImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImage


class PropertyTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyTag


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        fields = "__all__"


class ExcelDownloadFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcelDownloadFeedback
        fields = "__all__"


class ProjectOrganizationPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminArea
        fields = ("pcode", "path", "name")


class TestProjectSerializer(serializers.ModelSerializer):
    activity = serializers.SlugRelatedField(
        queryset=PropertyTag.objects.filter(path__startswith="ACT"),
        many=True,
        read_only=False,
        slug_field="name",
    )

    beneficiary = serializers.SlugRelatedField(
        queryset=PropertyTag.objects.filter(path__startswith="BEN"),
        many=True,
        read_only=False,
        slug_field="name",
    )

    sector = serializers.SlugRelatedField(
        queryset=PropertyTag.objects.filter(path__startswith="INV"),
        many=True,
        read_only=False,
        slug_field="name",
    )

    class Meta:
        model = Project
        exclude = ("place", "person", "organization")


class ProjectPropertiesSerializer(serializers.ModelSerializer):
    activity = serializers.SlugRelatedField(
        queryset=PropertyTag.objects.filter(path__startswith="ACT"),
        many=True,
        read_only=False,
        slug_field="name",
    )

    beneficiary = serializers.SlugRelatedField(
        queryset=PropertyTag.objects.filter(path__startswith="BEN"),
        many=True,
        read_only=False,
        slug_field="name",
    )

    sector = serializers.SlugRelatedField(
        queryset=PropertyTag.objects.filter(path__startswith="INV"),
        many=True,
        read_only=False,
        slug_field="name",
    )

    class Meta:
        model = Project
        fields = ("activity", "beneficiary", "sector")


class ProjectPropertiesSerializerByID(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "activity", "beneficiary", "sector")


class SuggestedChangeSerializer(serializers.ModelSerializer):
    def getrelatedchanges(self):
        """
        Get the model and the related primary key of other models which will change
        :return:
        """
        returns = []

        for name, field in self.fields.items():
            if hasattr(field, "queryset"):
                m = ".".join(
                    [
                        field.queryset.model._meta.app_label,
                        field.queryset.model._meta.model_name,
                    ]
                )
                returns.append((m, self.data.get(name)))
        return returns


class ProjectPersonSerializer(SuggestedChangeSerializer):
    project_title = serializers.SerializerMethodField()
    person_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPerson
        fields = (
            "id",
            "project",
            "person",
            "is_primary",
            "verified",
            "project_title",
            "person_name",
        )

    def get_project_title(self, obj):
        return obj.project.__unicode__()

    def get_person_name(self, obj):
        return obj.person.__unicode__()


class ProjectPlaceSerializer(serializers.ModelSerializer):
    project_title = serializers.SerializerMethodField()
    place_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPlace
        fields = (
            "id",
            "description",
            "project",
            "place",
            "project_title",
            "place_name",
        )
        validators = []  # Stop an error from being raised on Put or Patch requests

    def get_project_title(self, obj):
        return obj.project.__unicode__()

    def get_place_name(self, obj):
        return obj.place.__unicode__()


class ProjectProjectPlaceSerializer(serializers.ModelSerializer):
    projectplace_set = ProjectPlaceSerializer(many=True)

    class Meta:
        model = Project
        fields = ("projectplace_set",)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):

        projectplaces = validated_data.pop("projectplace_set")
        projectplace_ids = []
        for p in projectplaces:

            if p.get("id"):
                pp = ProjectPlace.objects.get(id=p.get("id"))
            else:
                pp = ProjectPlace.objects.get_or_create(
                    project=instance, place=p.get("place")
                )[0]

            pp.place = p.get("place")
            pp.project = p.get("project")
            pp.description = p.get("description")
            pp.save()
            projectplace_ids.append(pp.id)

            # Drop out any id's which have been removed
        dropped_places = instance.projectplace_set.exclude(pk__in=projectplace_ids)
        dropped_places.delete()

        return instance


class ProjectProjectPersonSerializer(serializers.ModelSerializer):
    projectperson_set = ProjectPersonSerializer(many=True)

    class Meta:
        model = Project
        fields = ("projectperson_set",)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):

        projectplaces = validated_data.pop("projectperson_set")
        projectperson_ids = []
        for p in projectplaces:

            if p.get("id"):
                pp = ProjectPerson.objects.get(id=p.get("id"))
            else:
                pp = ProjectPerson.objects.get_or_create(
                    project=instance, person=p.get("person")
                )[0]

            pp.person = p.get("person")
            pp.project = p.get("project")
            pp.description = p.get("description")
            pp.save()
            projectperson_ids.append(pp.id)

            # Drop out any id's which have been removed
        dropped_persons = instance.projectperson_set.exclude(pk__in=projectperson_ids)
        dropped_persons.delete()

        return instance


class ProjectProjectOrganizationSerializer(serializers.ModelSerializer):
    projectorganization_set = ProjectOrganizationSerializer(many=True, validators=[])

    class Meta:
        model = Project
        fields = ("projectorganization_set",)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        projectorganizations = validated_data.pop("projectorganization_set")
        for p in projectorganizations:
            po = ProjectOrganization.objects.get_or_create(
                project=instance, organization=p.get("organization")
            )
            po.comment = p.comment

        return instance


class PointField(serializers.Field):
    """
    Serialization of points is a comma separated x,y pair
    """

    def to_representation(self, obj):

        if not (obj.x and obj.y):
            return None

        lat, lng = obj.y, obj.x
        return "%f,%f" % (lng, lat)

    def to_internal_value(self, data):
        if not data:
            return None
        assert "," in data
        try:
            _lat, _lng = data.split(",")
            lng, lat = float(_lng), float(_lat)
        except ValueError:
            raise
        return Point(lat, lng)


class OrganizationPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPlace
        fields = ("description", "phone", "email", "id", "organization", "point")

    point = PointField()


class OrganizationOrganizationPlaceSerializer(serializers.ModelSerializer):
    organizationplace_set = OrganizationPlaceSerializer(many=True)

    class Meta:
        model = Organization
        fields = ("organizationplace_set",)

    def create(self, validated_data):
        model_class = self.Meta.model
        instance = validated_data["organizationplace_set"][0].get("organization")

        for op in validated_data["organizationplace_set"]:
            pass

        return instance

    def update(self, instance, validated_data):

        organizationplaces = validated_data.pop("organizationplace_set")
        organizationplace_ids = []
        for p in organizationplaces:

            if p.get("id"):
                pp = OrganizationPlace.objects.get(id=p.get("id"))
            else:
                pp = OrganizationPlace(organization=instance)

            for fieldName in ["point", "description", "phone", "email", "organization"]:
                setattr(pp, fieldName, p.get(fieldName))
                pp.place = p.get("place")
                pp.organization = p.get("organization")
                pp.point = p.get("point")
                pp.description = p.get("description")
            try:
                pp.place = Suco.objects.filter(geom__contains=pp.point)
            except:
                pp.place = None
            pp.save()
            organizationplace_ids.append(pp.id)

        # Drop out any id's which have been removed
        dropped_places = instance.organizationplace_set.exclude(
            pk__in=organizationplace_ids
        )
        dropped_places.delete()

        return instance
