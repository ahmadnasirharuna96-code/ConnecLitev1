import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import RegistrationChannel
from apps.ussd.services import handle_ussd_request

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestGuestUSSDFlow:
    def test_initial_dial_shows_welcome_menu(self):
        response = handle_ussd_request("sess-1", "+2348015550001", "")
        assert response.startswith("CON")
        assert "Register" in response

    def test_registration_flow_end_to_end(self):
        phone = "+2348015550002"
        # 1 = Register
        r1 = handle_ussd_request("sess-2", phone, "1")
        assert r1.startswith("CON")
        assert "name" in r1.lower()

        r2 = handle_ussd_request("sess-2", phone, "1*Aisha Bello")
        assert "age" in r2.lower()

        r3 = handle_ussd_request("sess-2", phone, "1*Aisha Bello*25")
        assert "gender" in r3.lower()

        r4 = handle_ussd_request("sess-2", phone, "1*Aisha Bello*25*2")
        assert "location" in r4.lower()

        r5 = handle_ussd_request("sess-2", phone, "1*Aisha Bello*25*2*Kano")
        assert "confirm" in r5.lower()

        r6 = handle_ussd_request("sess-2", phone, "1*Aisha Bello*25*2*Kano*1")
        assert r6.startswith("END")
        assert "Welcome to ConnectLite" in r6

        user = User.objects.get(phone_number=phone)
        assert user.registration_channel == RegistrationChannel.USSD
        assert user.is_phone_verified is True
        assert user.full_name == "Aisha Bello"

    def test_invalid_age_rejected(self):
        response = handle_ussd_request("sess-3", "+2348015550003", "1*Someone*999")
        assert response.startswith("END")
        assert "invalid age" in response.lower()

    def test_duplicate_registration_rejected(self, db):
        User.objects.create_user(phone_number="+2348015550004", password="x", full_name="Existing")
        response = handle_ussd_request(
            "sess-4", "+2348015550004", "1*New Name*30*1*Lagos*1"
        )
        assert response.startswith("END")
        assert "already exists" in response.lower()


@pytest.mark.django_db
class TestAuthenticatedUSSDFlow:
    def test_main_menu_for_registered_user(self, db):
        User.objects.create_user(
            phone_number="+2348015550005", password="x", full_name="Registered User", is_phone_verified=True
        )
        response = handle_ussd_request("sess-5", "+2348015550005", "")
        assert response.startswith("CON")
        assert "Find Connections" in response
        assert "Airtime" in response

    def test_find_connections_lists_candidates(self, db):
        user = User.objects.create_user(phone_number="+2348015550006", password="x", full_name="A", location="Jos")
        User.objects.create_user(phone_number="+2348015550007", password="x", full_name="B", location="Jos")
        response = handle_ussd_request("sess-6", "+2348015550006", "1")
        assert response.startswith("CON")
        assert "Top Connections" in response

    def test_my_profile_shows_details(self, db):
        User.objects.create_user(
            phone_number="+2348015550008", password="x", full_name="Profile User", location="Enugu"
        )
        response = handle_ussd_request("sess-7", "+2348015550008", "5")
        assert "Profile User" in response
        assert "Enugu" in response

    def test_help_ends_session(self, db):
        User.objects.create_user(phone_number="+2348015550009", password="x", full_name="Help User")
        response = handle_ussd_request("sess-8", "+2348015550009", "7")
        assert response.startswith("END")

    def test_invalid_menu_option(self, db):
        User.objects.create_user(phone_number="+2348015550010", password="x", full_name="X")
        response = handle_ussd_request("sess-9", "+2348015550010", "9")
        assert response.startswith("END")
        assert "invalid" in response.lower()


@pytest.mark.django_db
class TestUSSDWebhookView:
    def test_webhook_returns_plain_text_not_json(self, api_client):
        payload = {
            "sessionId": "sess-web-1",
            "phoneNumber": "+2348015550011",
            "serviceCode": "*384*1#",
            "text": "",
        }
        response = api_client.post(reverse("ussd:ussd-webhook"), payload)
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/plain")
        body = response.content.decode()
        assert body.startswith("CON") or body.startswith("END")

    def test_webhook_missing_fields_returns_end(self, api_client):
        response = api_client.post(reverse("ussd:ussd-webhook"), {"text": ""})
        body = response.content.decode()
        assert body.startswith("END")
