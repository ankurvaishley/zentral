from rest_framework import serializers
from .models import EnrollmentSecret, MetaBusinessUnit, Tag


# Machine mass tagging


class MachineTagsUpdatePrincipalUsers(serializers.Serializer):
    unique_ids = serializers.ListField(
        child=serializers.CharField(min_length=1),
        required=False
    )
    principal_names = serializers.ListField(
        child=serializers.CharField(min_length=1),
        required=False
    )

    def validate(self, data):
        if not data.get("unique_ids") and not data.get("principal_names"):
            raise serializers.ValidationError("Unique ids and principal names cannot be both empty.")
        return data


class MachineTagsUpdateSerializer(serializers.Serializer):
    tags = serializers.DictField(child=serializers.CharField(allow_null=True), allow_empty=False)
    principal_users = MachineTagsUpdatePrincipalUsers()


# Standard model serializers


class MetaBusinessUnitSerializer(serializers.ModelSerializer):
    api_enrollment_enabled = serializers.BooleanField(required=False)

    class Meta:
        model = MetaBusinessUnit
        fields = ("id", "name", "api_enrollment_enabled")
        read_only_fields = ("api_enrollment_enabled",)

    def validate_api_enrollment_enabled(self, value):
        if self.instance and self.instance.api_enrollment_enabled() and not value:
            raise serializers.ValidationError("Cannot disable API enrollment")
        return value

    def create(self, validated_data):
        api_enrollment_enabled = validated_data.pop("api_enrollment_enabled", False)
        mbu = super().create(validated_data)
        if api_enrollment_enabled:
            mbu.create_enrollment_business_unit()
        return mbu

    def update(self, instance, validated_data):
        api_enrollment_enabled = validated_data.pop("api_enrollment_enabled", False)
        mbu = super().update(instance, validated_data)
        if not mbu.api_enrollment_enabled() and api_enrollment_enabled:
            mbu.create_enrollment_business_unit()
        # TODO: switch off api_enrollment_enabled
        return mbu


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "meta_business_unit", "name", "slug", "color")
        # TODO: Taxonomy


class EnrollmentSecretSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrollmentSecret
        fields = ("id", "secret", "meta_business_unit", "tags", "serial_numbers", "udids", "quota", "request_count")
