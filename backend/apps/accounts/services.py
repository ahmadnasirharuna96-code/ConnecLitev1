"""
Service layer for accounts — keeps business logic out of views, per
the project's "no provider calls inside views" architecture rule.

NOTE (Phase 1 -> Phase 3 handoff):
`send_otp_sms` is a placeholder. In Phase 3 this will call
`integrations.africastalking.sms.SMSService.send_otp(...)` instead.
Nothing in views.py or serializers.py will need to change — that's
the point of the service-layer boundary.
"""
import logging

from django.conf import settings

from .models import OTPVerification

logger = logging.getLogger("connectlite")


class OTPThrottleError(Exception):
    """Raised when a new OTP is requested before the resend cooldown elapses."""


def request_otp(phone_number: str, purpose: str) -> OTPVerification:
    """
    Issue a fresh OTP for a phone number + purpose, enforcing the
    resend cooldown, and hand it off to the (currently stubbed)
    delivery channel. The plaintext code is never returned to callers
    outside this function, never logged, and never persisted.
    """
    cooldown = settings.OTP_SETTINGS["RESEND_COOLDOWN_SECONDS"]
    recent = (
        OTPVerification.objects.filter(phone_number=phone_number, purpose=purpose)
        .order_by("-created_at")
        .first()
    )
    if recent:
        from django.utils import timezone

        seconds_since = (timezone.now() - recent.created_at).total_seconds()
        if seconds_since < cooldown:
            raise OTPThrottleError(f"Please wait {int(cooldown - seconds_since)}s before requesting another code.")

    record, raw_code = OTPVerification.generate(phone_number=phone_number, purpose=purpose)
    _dispatch_otp(phone_number, raw_code)
    return record


def verify_otp(phone_number: str, code: str, purpose: str) -> bool:
    otp = (
        OTPVerification.objects.filter(
            phone_number=phone_number, purpose=purpose, is_used=False
        )
        .order_by("-created_at")
        .first()
    )
    if not otp:
        return False
    return otp.verify(code)


def _dispatch_otp(phone_number: str, raw_code: str) -> None:
    """
    Delivery boundary. The plaintext code is only ever passed to the SMS
    transport layer — never logged, never returned in an API response.
    """
    from integrations.africastalking.sms import SMSService

    try:
        result = SMSService.send_otp(phone_number, raw_code)
        if result.is_demo:
            logger.info("OTP dispatched to %s in DEMO MODE (no real SMS sent)", _mask_phone(phone_number))
        else:
            logger.info(
                "OTP dispatched to %s via Africa's Talking (provider_status=%s)",
                _mask_phone(phone_number),
                result.status,
            )
    except Exception as exc:  # noqa: BLE001
        # We deliberately do not re-raise: a transient SMS provider failure
        # shouldn't block registration/login flows that already validated
        # the phone number. The OTP record still exists and can be resent.
        logger.error("OTP dispatch to %s failed: %s", _mask_phone(phone_number), exc)


def _mask_phone(phone_number: str) -> str:
    if len(phone_number) <= 4:
        return "****"
    return f"{phone_number[:-4]}****"
