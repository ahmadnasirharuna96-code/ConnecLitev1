"""
Messaging service layer.

Routing rule: if the recipient registered via USSD (feature phone, no
app session to push into), messages are bridged out over SMS. Otherwise
they're stored as in-app messages, retrievable by polling — this is
intentionally NOT pretended to be real-time WebSocket chat, per the
project's messaging architecture requirement.

Inbound-SMS routing simplification (documented, hackathon-scope):
Africa's Talking delivers inbound SMS against a shared shortcode with no
built-in conversation-thread identifier. We resolve the sender by phone
number and route their message into their most recently active
conversation. A production version would establish a lightweight
reply-code protocol (e.g. "R <code> <message>") to disambiguate when a
feature-phone user has multiple open conversations.
"""
import logging

from django.contrib.auth import get_user_model

from apps.accounts.models import RegistrationChannel

from .models import Conversation, Message, MessageChannel, MessageStatus

logger = logging.getLogger("connectlite")
User = get_user_model()


def send_message(sender, recipient, content: str) -> Message:
    conversation = Conversation.get_or_create_for(sender, recipient)

    if recipient.registration_channel == RegistrationChannel.USSD:
        message = Message.objects.create(
            conversation=conversation, sender=sender, content=content, channel=MessageChannel.SMS,
            status=MessageStatus.PENDING,
        )
        _bridge_to_sms(message, sender, recipient, content)
    else:
        message = Message.objects.create(
            conversation=conversation, sender=sender, content=content, channel=MessageChannel.APP,
            status=MessageStatus.DELIVERED,
        )
        _notify_new_message(recipient, sender)

    conversation.save(update_fields=["updated_at"])
    return message


def _bridge_to_sms(message: Message, sender, recipient, content: str) -> None:
    from apps.notifications.models import SMSPurpose, SMSStatus
    from apps.notifications.services import send_sms_notification

    sms_record = send_sms_notification(
        recipient.phone_number,
        f"ConnectLite - {sender.full_name}: {content}",
        purpose=SMSPurpose.OFFLINE_MESSAGE,
    )
    message.status = MessageStatus.SENT if sms_record.status != SMSStatus.FAILED else MessageStatus.FAILED
    message.external_sms_id = sms_record.provider_message_id
    message.save(update_fields=["status", "external_sms_id"])


def _notify_new_message(recipient, sender) -> None:
    try:
        from apps.notifications.models import NotificationType
        from apps.notifications.services import notify_in_app

        notify_in_app(
            recipient, NotificationType.MESSAGE, title="New message", body=f"{sender.full_name} sent you a message."
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("In-app message notification failed: %s", exc)


def deliver_inbound_sms(from_phone: str, text: str) -> None:
    """Route an inbound SMS (from a feature-phone user) into a Message row."""
    try:
        sender = User.objects.get(phone_number=from_phone)
    except User.DoesNotExist:
        logger.warning("Inbound SMS from unregistered number %s — dropped.", _mask(from_phone))
        return

    conversation = Conversation.for_user(sender).order_by("-updated_at").first()
    if not conversation:
        logger.warning("Inbound SMS from %s has no active conversation to route into — dropped.", _mask(from_phone))
        return

    Message.objects.create(
        conversation=conversation, sender=sender, content=text, channel=MessageChannel.SMS,
        status=MessageStatus.DELIVERED,
    )
    conversation.save(update_fields=["updated_at"])

    recipient = conversation.other_participant(sender)
    _notify_new_message(recipient, sender)


def _mask(phone_number: str) -> str:
    if len(phone_number) <= 4:
        return "****"
    return f"{phone_number[:-4]}****"
