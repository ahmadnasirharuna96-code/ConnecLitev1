import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications.models import WebhookEvent
from apps.voice.models import VoiceVerification, VoiceVerificationStatus

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        phone_number="+2348017770001", password="Pass12345", full_name="Voice User", is_phone_verified=False
    )


@pytest.mark.django_db
class TestVoiceVerificationDemoMode:
    def test_start_verification_requires_auth(self, api_client):
        response = api_client.post(reverse("voice:start-verification"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_verification_demo_mode_auto_verifies(self, api_client, user, settings):
        settings.AFRICASTALKING["DEMO_MODE"] = True
        api_client.force_authenticate(user=user)
        response = api_client.post(reverse("voice:start-verification"))
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == VoiceVerificationStatus.VERIFIED
        assert response.data["is_demo"] is True

        user.refresh_from_db()
        assert user.is_phone_verified is True

    def test_verification_record_created(self, api_client, user):
        api_client.force_authenticate(user=user)
        api_client.post(reverse("voice:start-verification"))
        assert VoiceVerification.objects.filter(user=user).count() == 1


@pytest.mark.django_db
class TestVoiceWebhook:
    def test_webhook_records_event(self, api_client):
        response = api_client.post(reverse("voice:voice-webhook"), {"sessionId": "voice-sess-1"})
        assert response.status_code == status.HTTP_200_OK
        assert WebhookEvent.objects.filter(source="voice", provider_event_id="voice-sess-1").exists()

    def test_webhook_missing_id_rejected(self, api_client):
        response = api_client.post(reverse("voice:voice-webhook"), {})
        assert response.status_code == 400
