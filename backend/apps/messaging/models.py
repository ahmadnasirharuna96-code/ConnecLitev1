import uuid

from django.conf import settings
from django.db import models


class MessageChannel(models.TextChoices):
    APP = "app", "In-app"
    SMS = "sms", "SMS"


class MessageStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"


class Conversation(models.Model):
    """
    A conversation between exactly two users, stored with a canonical
    (participant_low, participant_high) ordering — same pattern as
    matching.Match — so a pair only ever has one conversation thread.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant_low = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_low"
    )
    participant_high = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_high"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "messaging_conversation"
        unique_together = ("participant_low", "participant_high")

    def other_participant(self, user):
        return self.participant_high if str(self.participant_low_id) == str(user.id) else self.participant_low

    @classmethod
    def get_or_create_for(cls, user_a, user_b):
        low, high = sorted([user_a, user_b], key=lambda u: str(u.id))
        conversation, _ = cls.objects.get_or_create(participant_low=low, participant_high=high)
        return conversation

    @classmethod
    def for_user(cls, user):
        return cls.objects.filter(models.Q(participant_low=user) | models.Q(participant_high=user))


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField(max_length=1000)
    channel = models.CharField(max_length=5, choices=MessageChannel.choices, default=MessageChannel.APP)
    status = models.CharField(max_length=10, choices=MessageStatus.choices, default=MessageStatus.PENDING)
    external_sms_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_message"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["conversation", "created_at"])]

    def __str__(self):
        return f"Message({self.sender_id} in {self.conversation_id}, {self.channel}/{self.status})"
