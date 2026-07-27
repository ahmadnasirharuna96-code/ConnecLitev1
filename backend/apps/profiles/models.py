import uuid
from datetime import date

from django.conf import settings
from django.db import models


class Interest(models.Model):
    """Catalog of interests users can attach to their profile."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "profiles_interest"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Profile(models.Model):
    """
    Extends User with profile-specific, mutable social data. Kept as a
    separate model (rather than bloating User) so identity/auth concerns
    stay isolated from social-profile concerns.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile", primary_key=True
    )
    bio = models.TextField(max_length=500, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", null=True, blank=True)
    interests = models.ManyToManyField(Interest, through="UserInterest", related_name="profiles", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles_profile"

    def __str__(self):
        return f"Profile<{self.user.full_name}>"

    @property
    def age(self):
        dob = self.user.date_of_birth
        if not dob:
            return None
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @property
    def verification_status(self):
        return "verified" if self.user.is_phone_verified else "unverified"


class UserInterest(models.Model):
    """Through-table for Profile <-> Interest, with an added timestamp."""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="user_interests")
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "profiles_user_interest"
        unique_together = ("profile", "interest")
