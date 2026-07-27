from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.profiles.serializers import PublicProfileSerializer

from .models import Conversation, Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.UUIDField(source="sender.id", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender_id", "content", "channel", "status", "created_at"]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "other_participant", "last_message", "updated_at"]
        read_only_fields = fields

    def get_other_participant(self, obj):
        user = self.context["request"].user
        other = obj.other_participant(user)
        return PublicProfileSerializer(other.profile).data

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        return MessageSerializer(last).data if last else None


class SendMessageSerializer(serializers.Serializer):
    to_user_id = serializers.UUIDField()
    content = serializers.CharField(max_length=1000)

    def validate_to_user_id(self, value):
        if not User.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("No such user.")
        return value
