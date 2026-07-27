import uuid

from django.conf import settings
from django.db import models


class CommunityCategory(models.TextChoices):
    UNIVERSITY = "university", "University"
    TECHNOLOGY = "technology", "Technology"
    BUSINESS = "business", "Business"
    PROFESSIONAL = "professional", "Professional"
    INTEREST = "interest", "Interest-based"
    LOCAL = "local", "Local"
    OTHER = "other", "Other"


class Community(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=1000, blank=True)
    category = models.CharField(max_length=20, choices=CommunityCategory.choices, default=CommunityCategory.OTHER)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="communities_created"
    )
    is_verified = models.BooleanField(default=False, help_text="Verified/sponsored community (business model tier).")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "communities_community"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.memberships.count()


class MembershipRole(models.TextChoices):
    MEMBER = "member", "Member"
    ADMIN = "admin", "Admin"


class CommunityMembership(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="community_memberships")
    role = models.CharField(max_length=10, choices=MembershipRole.choices, default=MembershipRole.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "communities_membership"
        unique_together = ("community", "user")

    def __str__(self):
        return f"{self.user_id} in {self.community.name} ({self.role})"
