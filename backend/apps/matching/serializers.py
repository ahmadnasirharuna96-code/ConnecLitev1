from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.profiles.serializers import PublicProfileSerializer

from .models import ConnectionRequest, Match

User = get_user_model()


class DiscoverUserSerializer(serializers.Serializer):
    """A candidate user surfaced by the discovery feed, with a compatibility score."""

    profile = serializers.SerializerMethodField()
    compatibility_score = serializers.IntegerField()

    def get_profile(self, obj):
        user = obj["user"]
        return PublicProfileSerializer(user.profile).data


class SendConnectionRequestSerializer(serializers.Serializer):
    to_user_id = serializers.UUIDField()

    def validate_to_user_id(self, value):
        if not User.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("No such user.")
        return value


class ConnectionRequestSerializer(serializers.ModelSerializer):
    from_user = serializers.SerializerMethodField()
    to_user = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionRequest
        fields = ["id", "from_user", "to_user", "status", "compatibility_score_snapshot", "created_at"]
        read_only_fields = fields

    def get_from_user(self, obj):
        return PublicProfileSerializer(obj.from_user.profile).data

    def get_to_user(self, obj):
        return PublicProfileSerializer(obj.to_user.profile).data


class RespondConnectionRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["accept", "reject"])


class MatchSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = ["id", "other_user", "compatibility_score", "created_at"]
        read_only_fields = fields

    def get_other_user(self, obj):
        request_user = self.context["request"].user
        other = obj.other_user(request_user)
        return PublicProfileSerializer(other.profile).data
