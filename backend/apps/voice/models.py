import uuid

from django.conf import settings
from django.db import models


class VoiceVerificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    VERIFIED = "verified", "Verified"
    FAILED = "failed", "Failed"


class VoiceVerification(models.Model):
    """
    Voice-based verification record. Kept minimal and demo-mode-only in
    this build — see integrations/africastalking/voice.py docstring for
    why the live call flow isn't implemented here.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="voice_verifications")
    status = models.CharField(max_length=10, choices=VoiceVerificationStatus.choices, default=VoiceVerificationStatus.PENDING)
    provider_call_id = models.CharField(max_length=100, blank=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "voice_verification"

    def __str__(self):
        return f"VoiceVerification({self.user_id}, {self.status})"
