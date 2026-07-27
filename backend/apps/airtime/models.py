import uuid

from django.conf import settings
from django.db import models


class AirtimeStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


class AirtimePurpose(models.TextChoices):
    GIFT = "gift", "Gift"
    REFERRAL_REWARD = "referral_reward", "Referral Reward"
    COMMUNITY_REWARD = "community_reward", "Community Reward"


class AirtimeTransaction(models.Model):
    """
    Every airtime movement — gifts, referral rewards, community rewards —
    goes through this single ledger, regardless of purpose, so abuse
    checks (duplicate/self-reward/replay prevention) have one place to
    look.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="airtime_sent", help_text="Null for system-initiated rewards (referral/community).",
    )
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="airtime_received")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    purpose = models.CharField(max_length=20, choices=AirtimePurpose.choices, default=AirtimePurpose.GIFT)
    status = models.CharField(max_length=10, choices=AirtimeStatus.choices, default=AirtimeStatus.PENDING)
    provider_transaction_id = models.CharField(max_length=100, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "airtime_transaction"
        indexes = [
            models.Index(fields=["recipient", "status"]),
            models.Index(fields=["sender", "status"]),
        ]

    def __str__(self):
        return f"Airtime({self.amount} {self.currency} -> {self.recipient_id}, {self.status})"
