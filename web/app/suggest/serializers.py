from rest_framework import serializers
from models import Suggest, AffectedInstance


class AffectedInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffectedInstance
        fields = ("model_name", "model_pk", "primary")


class SuggestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suggest
        fields = "__all__"

    def create(self, validated_data):

        instances = validated_data.pop("affectedinstance_set")

        s = Suggest.objects.create(**validated_data)

        # A 'Create Model' call must include a suggestedinstance with a model_name and primary=True, blank model_pk
        if s.action == "CM":
            for i in instances:
                if i["primary"] and i["model_name"]:
                    break
                raise AssertionError(
                    "You must pass a primary model name with primary=True specified!"
                )

        for i in instances:
            AffectedInstance.objects.create(suggestion=s, **i)

        s.set_uploaded_files()
        return s

    def update(self, instance, validated_data):

        try:
            validated_data.pop("affectedinstance_set")
        except KeyError:
            pass

        # Action to take on the creation of a model
        #  The request must include a created model PK
        if instance.action == "CM" and validated_data.get("state") == "A":
            ai = instance.primary
            ai.model_pk = self.initial_data.get("created_model_pk", None)
            assert ai.model_pk, "created model_pk not given! Initial data was %s" % (
                self.initial_data
            )
            # ai.model_pk = self.context['request'].POST['created_model_pk']
            ai.save()

        elif instance.action == "UM" and validated_data.get("state") == "A":
            pass

        elif instance.action == "DM" and validated_data["state"] == "A":
            try:
                ai = AffectedInstance.objects.get(suggestion=instance, primary=True)
                ai.remove()
            except:
                pass

        elif validated_data["state"] == "X":
            pass

        elif validated_data["state"] == "R":
            # Rejected
            pass

        else:
            raise NotImplementedError(
                "{} {}".format(instance.action, validated_data["state"])
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.set_uploaded_files()
        return instance

    affectedinstance_set = AffectedInstanceSerializer(many=True, read_only=False)
