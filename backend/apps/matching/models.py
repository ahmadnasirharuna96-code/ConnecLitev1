import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ConnectionRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class ConnectionRequest(models.Model):
    """A one-directional connection request from one user to another."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_connection_requests"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_connection_requests"
    )
    status = models.CharField(max_length=10, choices=ConnectionRequestStatus.choices, default=ConnectionRequestStatus.PENDING)
    compatibility_score_snapshot = models.FloatField(
        null=True, blank=True, help_text="Compatibility score at the time this request was sent."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "matching_connection_request"
        unique_together = ("from_user", "to_user")
        indexes = [models.Index(fields=["to_user", "status"])]

    def clean(self):
        if self.from_user_id == self.to_user_id:
            raise ValidationError("A user cannot send a connection request to themselves.")

    def __str__(self):
        return f"{self.from_user_id} -> {self.to_user_id} ({self.status})"


class Match(models.Model):
    """
    A mutual, confirmed connection between two users. Stored with a
    canonical (user_low, user_high) ordering — by string PK comparison —
    so a pair can never produce two duplicate Match rows.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_low = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="matches_as_low")
    user_high = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="matches_as_high")
    compatibility_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "matching_match"
        unique_together = ("user_low", "user_high")
        indexes = [models.Index(fields=["user_low"]), models.Index(fields=["user_high"])]

    def __str__(self):
        return f"Match({self.user_low_id}, {self.user_high_id}) = {self.compatibility_score}%"

    @classmethod
    def get_or_create_for(cls, user_a, user_b, score):
        low, high = sorted([user_a, user_b], key=lambda u: str(u.id))
        match, created = cls.objects.get_or_create(
            user_low=low, user_high=high, defaults={"compatibility_score": score}
        )
        return match, created

    def other_user(self, user):
        return self.user_high if str(self.user_low_id) == str(user.id) else self.user_low

    @classmethod
    def for_user(cls, user):
        return cls.objects.filter(models.Q(user_low=user) | models.Q(user_high=user))
