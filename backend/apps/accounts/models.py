import hashlib
import secrets
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class RegistrationChannel(models.TextChoices):
    WEB = "web", "Web / Smartphone"
    USSD = "ussd", "USSD / Feature Phone"


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"


class User(AbstractBaseUser, PermissionsMixin):
    """
    ConnectLite's custom user. Phone number is the primary identifier
    since it is the one credential every user has, regardless of
    whether they access ConnectLite via web/app or USSD/SMS.

    IMPORTANT: every FK to the user across the codebase MUST reference
    settings.AUTH_USER_MODEL, never this class directly.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    location = models.CharField(max_length=150, blank=True)

    registration_channel = models.CharField(
        max_length=10, choices=RegistrationChannel.choices, default=RegistrationChannel.WEB
    )

    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    referral_code = models.CharField(
        max_length=10, unique=True, blank=True,
        help_text="Auto-generated, shareable code other users can enter at registration.",
    )
    referred_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals",
        help_text="The user whose referral_code this user entered at registration, if any.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "accounts_user"
        indexes = [models.Index(fields=["phone_number"]), models.Index(fields=["referral_code"])]

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_unique_referral_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_unique_referral_code() -> str:
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I — avoids USSD/SMS misreads
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(6))
            if not User.objects.filter(referral_code=code).exists():
                return code

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


class OTPPurpose(models.TextChoices):
    REGISTRATION = "registration", "Registration"
    LOGIN = "login", "Login"
    VOICE_VERIFICATION = "voice_verification", "Voice Verification"
    PASSWORD_RESET = "password_reset", "Password Reset"


class OTPVerification(models.Model):
    """
    Stores only a salted hash of the OTP code — the plaintext code is
    never persisted, logged, or returned in any API response. It is
    only ever transmitted once, over SMS (or voice, in Phase 6).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, db_index=True)
    purpose = models.CharField(max_length=30, choices=OTPPurpose.choices)

    code_hash = models.CharField(max_length=64)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)

    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_otp_verification"
        indexes = [models.Index(fields=["phone_number", "purpose", "is_used"])]

    def __str__(self):
        return f"OTP({self.phone_number}, {self.purpose}, used={self.is_used})"

    # ---- helpers -----------------------------------------------------

    @staticmethod
    def hash_code(raw_code: str) -> str:
        return hashlib.sha256(raw_code.encode("utf-8")).hexdigest()

    @classmethod
    def generate(cls, phone_number: str, purpose: str) -> tuple["OTPVerification", str]:
        """Create a new OTP record and return (record, plaintext_code)."""
        length = settings.OTP_SETTINGS["LENGTH"]
        expiry_minutes = settings.OTP_SETTINGS["EXPIRY_MINUTES"]
        max_attempts = settings.OTP_SETTINGS["MAX_ATTEMPTS"]

        raw_code = "".join(secrets.choice("0123456789") for _ in range(length))
        record = cls.objects.create(
            phone_number=phone_number,
            purpose=purpose,
            code_hash=cls.hash_code(raw_code),
            max_attempts=max_attempts,
            expires_at=timezone.now() + timezone.timedelta(minutes=expiry_minutes),
        )
        return record, raw_code

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def verify(self, raw_code: str) -> bool:
        """Check code validity. Increments attempts on failure. Marks used on success."""
        if self.is_used or self.is_expired() or self.attempts >= self.max_attempts:
            return False

        if self.code_hash == self.hash_code(raw_code):
            self.is_used = True
            self.save(update_fields=["is_used"])
            return True

        self.attempts += 1
        self.save(update_fields=["attempts"])
        return False
