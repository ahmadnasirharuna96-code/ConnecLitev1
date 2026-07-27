from rest_framework import serializers

from .models import Notification, SMSPurpose


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "notification_type", "title", "body", "is_read", "created_at"]
        read_only_fields = fields


class SendSMSNotificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    message = serializers.CharField(max_length=480)
    purpose = serializers.ChoiceField(choices=SMSPurpose.choices, required=False)
