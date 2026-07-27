import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications.models import SMSMessage, SMSStatus, WebhookEvent
from apps.notifications.services import send_sms_notification

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestSMSNotificationService:
    def test_send_sms_notification_demo_mode_succeeds(self, settings):
        settings.AFRICASTALKING["DEMO_MODE"] = True
        record = send_sms_notification("+2348012340000", "Hello from ConnectLite")
        assert record.status == SMSStatus.SENT
        assert record.is_demo is True
        assert record.provider_message_id.startswith("DEMO-")

    def test_sms_body_is_previewed_not_leaked_in_full_when_over_160(self, settings):
        settings.AFRICASTALKING["DEMO_MODE"] = True
        long_message = "x" * 300
        record = send_sms_notification("+2348012340001", long_message)
        assert len(record.body_preview) <= 160


@pytest.mark.django_db
class TestSMSWebhooks:
    def test_delivery_webhook_updates_status_and_is_idempotent(self, api_client):
        sms = SMSMessage.objects.create(
            recipient_phone="+2348012340002", provider_message_id="ATXid_123", status=SMSStatus.SENT
        )
        payload = {"id": "ATXid_123", "status": "Success", "phoneNumber": "+2348012340002"}

        first = api_client.post(reverse("notifications:sms-delivery-webhook"), payload)
        assert first.status_code == status.HTTP_200_OK
        sms.refresh_from_db()
        assert sms.status == SMSStatus.DELIVERED
        assert WebhookEvent.objects.filter(source="sms_delivery").count() == 1

        # Redelivery of the same webhook must be a no-op, not double-processed.
        second = api_client.post(reverse("notifications:sms-delivery-webhook"), payload)
        assert second.status_code == status.HTTP_200_OK
        assert WebhookEvent.objects.filter(source="sms_delivery").count() == 1

    def test_incoming_sms_webhook_creates_webhook_event(self, api_client, db):
        User.objects.create_user(phone_number="+2348012340003", password="Pass12345", full_name="Feature Phone User")
        payload = {"id": "msg-abc-1", "from": "+2348012340003", "to": "12345", "text": "hello there", "date": "now"}

        response = api_client.post(reverse("notifications:sms-incoming-webhook"), payload)
        assert response.status_code == status.HTTP_200_OK
        assert WebhookEvent.objects.filter(source="sms_incoming", provider_event_id="msg-abc-1").exists()

        # Redelivery is idempotent.
        api_client.post(reverse("notifications:sms-incoming-webhook"), payload)
        assert WebhookEvent.objects.filter(source="sms_incoming", provider_event_id="msg-abc-1").count() == 1
