from rest_framework import serializers

from .models import VoiceVerification


class VoiceVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceVerification
        fields = ["id", "status", "is_demo", "created_at", "updated_at"]
        read_only_fields = fields
