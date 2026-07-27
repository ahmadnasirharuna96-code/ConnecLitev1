"""
SMS integration — the only place that sends SMS via Africa's Talking
(or, in demo mode, a local mock that never leaves the process).
"""
import logging
import uuid

from django.conf import settings

from .client import get_sdk, is_demo_mode
from .exceptions import SMSDeliveryError

logger = logging.getLogger("connectlite")


class SMSResult:
    def __init__(self, success: bool, provider_message_id: str, status: str, is_demo: bool):
        self.success = success
        self.provider_message_id = provider_message_id
        self.status = status  # Sent / Success / Failed (provider vocabulary) or DEMO
        self.is_demo = is_demo


class SMSService:
    """Thin, testable wrapper around Africa's Talking SMS."""

    @staticmethod
    def send(phone_number: str, message: str) -> SMSResult:
        if is_demo_mode():
            return SMSService._send_demo(phone_number, message)
        return SMSService._send_live(phone_number, message)

    @staticmethod
    def _send_demo(phone_number: str, message: str) -> SMSResult:
        fake_id = f"DEMO-{uuid.uuid4().hex[:12]}"
        logger.info(
            "[DEMO MODE] Would send SMS to %s (%d chars) — no real message sent. provider_message_id=%s",
            SMSService._mask(phone_number),
            len(message),
            fake_id,
        )
        return SMSResult(success=True, provider_message_id=fake_id, status="DEMO", is_demo=True)

    @staticmethod
    def _send_live(phone_number: str, message: str) -> SMSResult:
        sdk = get_sdk()
        sms = sdk.SMS
        sender_id = settings.AFRICASTALKING["SENDER_ID"] or None
        try:
            response = sms.send(message, [phone_number], sender_id=sender_id)
            recipients = response.get("SMSMessageData", {}).get("Recipients", [])
            if not recipients:
                raise SMSDeliveryError("Africa's Talking returned no recipient data.")
            recipient = recipients[0]
            success = str(recipient.get("statusCode")) == "101"  # AT: 101 == queued/sent successfully
            return SMSResult(
                success=success,
                provider_message_id=recipient.get("messageId", ""),
                status=recipient.get("status", "Unknown"),
                is_demo=False,
            )
        except Exception as exc:  # noqa: BLE001 — deliberately broad: any provider failure must not crash the caller
            logger.error("Africa's Talking SMS send failed: %s", exc)
            raise SMSDeliveryError(str(exc)) from exc

    @staticmethod
    def send_otp(phone_number: str, code: str) -> SMSResult:
        expiry = settings.OTP_SETTINGS["EXPIRY_MINUTES"]
        message = f"Your ConnectLite verification code is {code}. It expires in {expiry} minutes."
        return SMSService.send(phone_number, message)

    @staticmethod
    def _mask(phone_number: str) -> str:
        if len(phone_number) <= 4:
            return "****"
        return f"{phone_number[:-4]}****"
