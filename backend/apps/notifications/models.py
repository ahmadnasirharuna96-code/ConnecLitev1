import uuid

from django.conf import settings
from django.db import models


class SMSStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"


class SMSPurpose(models.TextChoices):
    OTP = "otp", "OTP"
    MATCH_NOTIFICATION = "match_notification", "Match Notification"
    FRIEND_REQUEST = "friend_request", "Friend Request"
    MESSAGE_NOTIFICATION = "message_notification", "Message Notification"
    COMMUNITY_NOTIFICATION = "community_notification", "Community Notification"
    OFFLINE_MESSAGE = "offline_message", "Offline Messaging (SMS bridge)"
    OTHER = "other", "Other"


class SMSMessage(models.Model):
    """
    Outbound SMS log. The OTP purpose intentionally never stores the
    OTP code itself in `body` — see apps.accounts.services — this model
    exists for delivery tracking, not for reconstructing message content.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient_phone = models.CharField(max_length=20, db_index=True)
    purpose = models.CharField(max_length=30, choices=SMSPurpose.choices, default=SMSPurpose.OTHER)
    body_preview = models.CharField(
        max_length=160, blank=True, help_text="Non-sensitive preview only — never store OTP codes here."
    )
    status = models.CharField(max_length=10, choices=SMSStatus.choices, default=SMSStatus.PENDING)
    provider_message_id = models.CharField(max_length=100, blank=True, db_index=True)
    is_demo = models.BooleanField(default=False)
    error_message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notifications_sms_message"
        indexes = [models.Index(fields=["recipient_phone", "purpose"])]

    def __str__(self):
        return f"SMS({self.recipient_phone}, {self.purpose}, {self.status})"


class WebhookEvent(models.Model):
    """
    Records every inbound webhook call from Africa's Talking so handlers
    can be made idempotent — a provider event is only ever processed once,
    regardless of how many times it's retried/redelivered.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=30, help_text="e.g. 'sms_incoming', 'sms_delivery', 'ussd', 'voice'")
    provider_event_id = models.CharField(
        max_length=150, unique=True, help_text="Provider-supplied unique ID used for idempotency."
    )
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_webhook_event"
        indexes = [models.Index(fields=["source", "processed"])]

    def __str__(self):
        return f"WebhookEvent({self.source}, {self.provider_event_id})"


class NotificationType(models.TextChoices):
    MATCH = "match", "Match"
    CONNECTION_REQUEST = "connection_request", "Connection Request"
    MESSAGE = "message", "Message"
    COMMUNITY = "community", "Community"
    AIRTIME = "airtime", "Airtime"
    SYSTEM = "system", "System"


class Notification(models.Model):
    """In-app notification feed entry (separate from the SMS transport log above)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    title = models.CharField(max_length=150)
    body = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"Notification({self.user_id}, {self.notification_type})"
