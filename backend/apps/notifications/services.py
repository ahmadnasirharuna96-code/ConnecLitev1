"""
Notification service layer — the single place business logic (matching,
messaging, communities, airtime) goes to notify a user, whether that
notification ends up as an in-app Notification row, an SMS, or both.
"""
import logging

from .models import Notification, NotificationType, SMSMessage, SMSPurpose, SMSStatus

logger = logging.getLogger("connectlite")


def notify_in_app(user, notification_type: str, title: str, body: str = "") -> Notification:
    return Notification.objects.create(user=user, notification_type=notification_type, title=title, body=body)


def send_sms_notification(phone_number: str, message: str, purpose: str = SMSPurpose.OTHER) -> SMSMessage:
    """
    Sends an SMS via the Africa's Talking integration layer and logs the
    attempt/result. Never stores full message bodies that could contain
    sensitive data (e.g. OTP codes) — callers handling OTPs should use
    apps.accounts.services instead, which never routes through here.
    """
    from integrations.africastalking.sms import SMSService

    record = SMSMessage.objects.create(
        recipient_phone=phone_number,
        purpose=purpose,
        body_preview=message[:160],
        status=SMSStatus.PENDING,
    )
    try:
        result = SMSService.send(phone_number, message)
        record.status = SMSStatus.SENT if result.success else SMSStatus.FAILED
        record.provider_message_id = result.provider_message_id
        record.is_demo = result.is_demo
        record.save(update_fields=["status", "provider_message_id", "is_demo", "updated_at"])
    except Exception as exc:  # noqa: BLE001
        record.status = SMSStatus.FAILED
        record.error_message = str(exc)[:255]
        record.save(update_fields=["status", "error_message", "updated_at"])
        logger.error("SMS notification to %s failed: %s", phone_number, exc)
    return record


def notify_match(user_a, user_b) -> None:
    for user, other in [(user_a, user_b), (user_b, user_a)]:
        notify_in_app(
            user,
            NotificationType.MATCH,
            title="New match!",
            body=f"You matched with {other.full_name}.",
        )
        send_sms_notification(
            user.phone_number,
            f"ConnectLite: You have a new match with {other.full_name}! Open the app to say hello.",
            purpose=SMSPurpose.MATCH_NOTIFICATION,
        )


def notify_connection_request(to_user, from_user) -> None:
    notify_in_app(
        to_user,
        NotificationType.CONNECTION_REQUEST,
        title="New connection request",
        body=f"{from_user.full_name} wants to connect with you.",
    )
    send_sms_notification(
        to_user.phone_number,
        f"ConnectLite: {from_user.full_name} sent you a connection request. Open the app to respond.",
        purpose=SMSPurpose.FRIEND_REQUEST,
    )
