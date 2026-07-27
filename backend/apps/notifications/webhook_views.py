"""
Africa's Talking webhook receivers.

Design rules (see project security requirements):
  - Every handler is idempotent: a WebhookEvent row is created keyed on
    the provider's own event/message ID; a redelivered webhook is a
    no-op the second time.
  - Never expose secrets or internal error detail in the response.
  - Always return an HTTP response the provider expects, even on
    internal errors, so AT doesn't endlessly retry a request we can't
    process.
"""
import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SMSMessage, SMSStatus, WebhookEvent

logger = logging.getLogger("connectlite")


class SMSIncomingWebhookView(APIView):
    """
    POST /api/v1/webhooks/africastalking/sms/incoming/

    Handles inbound SMS from feature-phone users (the SMS half of the
    smartphone <-> feature-phone messaging bridge). Africa's Talking
    posts form-encoded fields: from, to, text, date, id, linkId.
    """

    permission_classes = [AllowAny]
    parser_classes = [FormParser, JSONParser]
    authentication_classes = []

    def post(self, request):
        data = request.data
        provider_event_id = str(data.get("id") or data.get("linkId") or "")
        from_phone = data.get("from", "")
        text = data.get("text", "")

        if not provider_event_id:
            return Response({"error": "missing message id"}, status=400)

        event, created = WebhookEvent.objects.get_or_create(
            source="sms_incoming",
            provider_event_id=provider_event_id,
            defaults={"payload": dict(data)},
        )
        if not created and event.processed:
            # Already handled — idempotent no-op.
            return Response({"status": "already_processed"})

        try:
            self._process(from_phone, text)
            event.processed = True
            event.save(update_fields=["processed"])
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to process incoming SMS webhook %s: %s", provider_event_id, exc)
            # Return 200 anyway — AT will retry indefinitely on non-2xx,
            # and we've already durably recorded the event for investigation.

        return Response({"status": "received"})

    def _process(self, from_phone: str, text: str) -> None:
        from apps.messaging.services import deliver_inbound_sms

        deliver_inbound_sms(from_phone, text)


class SMSDeliveryWebhookView(APIView):
    """
    POST /api/v1/webhooks/africastalking/sms/delivery/

    Africa's Talking posts delivery reports: id, status, phoneNumber,
    networkCode, failureReason.
    """

    permission_classes = [AllowAny]
    parser_classes = [FormParser, JSONParser]
    authentication_classes = []

    STATUS_MAP = {
        "Success": SMSStatus.DELIVERED,
        "Sent": SMSStatus.SENT,
        "Submitted": SMSStatus.SENT,
        "Buffered": SMSStatus.PENDING,
        "Rejected": SMSStatus.FAILED,
        "Failed": SMSStatus.FAILED,
        "InsufficientBalance": SMSStatus.FAILED,
        "UserInBlacklist": SMSStatus.FAILED,
    }

    def post(self, request):
        data = request.data
        provider_message_id = str(data.get("id", ""))
        provider_status = data.get("status", "")

        if not provider_message_id:
            return Response({"error": "missing message id"}, status=400)

        event, created = WebhookEvent.objects.get_or_create(
            source="sms_delivery",
            provider_event_id=f"{provider_message_id}:{provider_status}",
            defaults={"payload": dict(data)},
        )
        if not created and event.processed:
            return Response({"status": "already_processed"})

        SMSMessage.objects.filter(provider_message_id=provider_message_id).update(
            status=self.STATUS_MAP.get(provider_status, SMSStatus.SENT)
        )
        event.processed = True
        event.save(update_fields=["processed"])
        return Response({"status": "received"})
