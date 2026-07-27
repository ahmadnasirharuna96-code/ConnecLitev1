from rest_framework import serializers

from .models import Interest, Profile


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ["id", "name", "category"]


class ProfileSerializer(serializers.ModelSerializer):
    """Full profile view/edit for the *owning* user (includes editable fields)."""

    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    date_of_birth = serializers.DateField(source="user.date_of_birth", required=False)
    gender = serializers.CharField(source="user.gender", required=False)
    location = serializers.CharField(source="user.location", required=False)
    age = serializers.IntegerField(read_only=True)
    verification_status = serializers.CharField(read_only=True)
    interests = InterestSerializer(many=True, read_only=True)
    interest_ids = serializers.PrimaryKeyRelatedField(
        source="interests", queryset=Interest.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Profile
        fields = [
            "full_name",
            "phone_number",
            "email",
            "bio",
            "occupation",
            "profile_photo",
            "date_of_birth",
            "gender",
            "location",
            "age",
            "verification_status",
            "interests",
            "interest_ids",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        interests = validated_data.pop("interests", None)

        user = instance.user
        for field, value in user_data.items():
            setattr(user, field, value)
        if user_data:
            user.save(update_fields=list(user_data.keys()))

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if interests is not None:
            instance.interests.set(interests)

        return instance


class PublicProfileSerializer(serializers.ModelSerializer):
    """Limited-exposure view of *other* users' profiles — no phone/email."""

    id = serializers.UUIDField(source="user.id", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    gender = serializers.CharField(source="user.gender", read_only=True)
    location = serializers.CharField(source="user.location", read_only=True)
    age = serializers.IntegerField(read_only=True)
    verification_status = serializers.CharField(read_only=True)
    interests = InterestSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "full_name",
            "bio",
            "occupation",
            "profile_photo",
            "gender",
            "location",
            "age",
            "verification_status",
            "interests",
        ]
        read_only_fields = fields
