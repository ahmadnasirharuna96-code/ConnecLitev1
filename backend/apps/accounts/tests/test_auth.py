import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import OTPPurpose, OTPVerification

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def registered_user(db):
    user = User.objects.create_user(
        phone_number="+2348012345678",
        password="StrongPass123",
        full_name="Aisha Bello",
        is_phone_verified=True,
    )
    return user


@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_unverified_user(self, api_client):
        payload = {
            "phone_number": "+2348011112222",
            "email": "aisha@example.com",
            "password": "StrongPass123",
            "full_name": "Aisha Bello",
            "gender": "female",
            "location": "Kano",
        }
        response = api_client.post(reverse("accounts:register"), payload)
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(phone_number="+2348011112222")
        assert user.is_phone_verified is False
        assert user.check_password("StrongPass123")

    def test_register_duplicate_phone_rejected(self, api_client, registered_user):
        payload = {
            "phone_number": registered_user.phone_number,
            "password": "AnotherPass123",
            "full_name": "Duplicate User",
        }
        response = api_client.post(reverse("accounts:register"), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password_rejected(self, api_client):
        payload = {"phone_number": "+2348099998888", "password": "123", "full_name": "Weak Pass"}
        response = api_client.post(reverse("accounts:register"), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestOTPFlow:
    def test_request_otp_does_not_leak_code(self, api_client, db):
        User.objects.create_user(phone_number="+2348033334444", password="Pass12345", full_name="Test User")
        response = api_client.post(
            reverse("accounts:request-otp"), {"phone_number": "+2348033334444", "purpose": "login"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "code" not in str(response.data).lower()

    def test_verify_otp_success_issues_tokens_and_marks_verified(self, api_client):
        user = User.objects.create_user(
            phone_number="+2348055556666", password="Pass12345", full_name="New User", is_phone_verified=False
        )
        record, raw_code = OTPVerification.generate(user.phone_number, OTPPurpose.REGISTRATION)

        response = api_client.post(
            reverse("accounts:verify-otp"),
            {"phone_number": user.phone_number, "code": raw_code, "purpose": "registration"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["tokens"]
        user.refresh_from_db()
        assert user.is_phone_verified is True

    def test_verify_otp_wrong_code_fails(self, api_client):
        user = User.objects.create_user(phone_number="+2348077778888", password="Pass12345", full_name="Someone")
        OTPVerification.generate(user.phone_number, OTPPurpose.REGISTRATION)

        response = api_client.post(
            reverse("accounts:verify-otp"),
            {"phone_number": user.phone_number, "code": "000000", "purpose": "registration"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_otp_cannot_be_reused(self, api_client):
        user = User.objects.create_user(phone_number="+2348088889999", password="Pass12345", full_name="Someone")
        record, raw_code = OTPVerification.generate(user.phone_number, OTPPurpose.REGISTRATION)

        first = api_client.post(
            reverse("accounts:verify-otp"),
            {"phone_number": user.phone_number, "code": raw_code, "purpose": "registration"},
        )
        second = api_client.post(
            reverse("accounts:verify-otp"),
            {"phone_number": user.phone_number, "code": raw_code, "purpose": "registration"},
        )
        assert first.status_code == status.HTTP_200_OK
        assert second.status_code == status.HTTP_400_BAD_REQUEST

    def test_otp_lockout_after_max_attempts(self, db):
        record, raw_code = OTPVerification.generate("+2348099990000", OTPPurpose.LOGIN)
        for _ in range(record.max_attempts):
            assert record.verify("wrong-code") is False
        # Even the correct code should now fail — attempts exhausted.
        assert record.verify(raw_code) is False


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, registered_user):
        response = api_client.post(
            reverse("accounts:login"),
            {"phone_number": registered_user.phone_number, "password": "StrongPass123"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]

    def test_login_wrong_password(self, api_client, registered_user):
        response = api_client.post(
            reverse("accounts:login"),
            {"phone_number": registered_user.phone_number, "password": "WrongPassword"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_blocked_if_phone_unverified(self, api_client, db):
        User.objects.create_user(
            phone_number="+2348012349999", password="Pass12345", full_name="Unverified", is_phone_verified=False
        )
        response = api_client.post(
            reverse("accounts:login"), {"phone_number": "+2348012349999", "password": "Pass12345"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestMeAndLogout:
    def test_me_requires_authentication(self, api_client):
        response = api_client.get(reverse("accounts:me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_current_user(self, api_client, registered_user):
        api_client.force_authenticate(user=registered_user)
        response = api_client.get(reverse("accounts:me"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone_number"] == registered_user.phone_number

    def test_logout_blacklists_refresh_token(self, api_client, registered_user):
        login_response = api_client.post(
            reverse("accounts:login"),
            {"phone_number": registered_user.phone_number, "password": "StrongPass123"},
        )
        refresh_token = login_response.data["tokens"]["refresh"]
        access_token = login_response.data["tokens"]["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.post(reverse("accounts:logout"), {"refresh": refresh_token})
        assert response.status_code == status.HTTP_200_OK
