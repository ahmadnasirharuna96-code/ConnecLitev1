import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import OTPPurpose, OTPVerification
from apps.airtime.models import AirtimePurpose, AirtimeTransaction

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestReferralCodeGeneration:
    def test_every_user_gets_a_unique_referral_code(self):
        a = User.objects.create_user(phone_number="+2348018880001", password="Pass12345", full_name="A")
        b = User.objects.create_user(phone_number="+2348018880002", password="Pass12345", full_name="B")
        assert a.referral_code
        assert b.referral_code
        assert a.referral_code != b.referral_code
        assert len(a.referral_code) == 6


@pytest.mark.django_db
class TestReferralRegistrationFlow:
    def test_register_with_valid_referral_code(self, api_client):
        referrer = User.objects.create_user(phone_number="+2348018880003", password="Pass12345", full_name="Referrer")

        response = api_client.post(
            reverse("accounts:register"),
            {
                "phone_number": "+2348018880004",
                "password": "StrongPass123",
                "full_name": "Referred User",
                "referred_by_code": referrer.referral_code.lower(),  # case-insensitive
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        referred = User.objects.get(phone_number="+2348018880004")
        assert referred.referred_by_id == referrer.id

    def test_register_with_invalid_referral_code_rejected(self, api_client):
        response = api_client.post(
            reverse("accounts:register"),
            {
                "phone_number": "+2348018880005",
                "password": "StrongPass123",
                "full_name": "Someone",
                "referred_by_code": "BADCODE",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_without_referral_code_still_works(self, api_client):
        response = api_client.post(
            reverse("accounts:register"),
            {"phone_number": "+2348018880006", "password": "StrongPass123", "full_name": "No Referral"},
        )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestReferralRewardOnVerification:
    def test_referrer_rewarded_when_referred_user_verifies_phone(self, api_client, settings):
        settings.AFRICASTALKING["DEMO_MODE"] = True
        referrer = User.objects.create_user(phone_number="+2348018880007", password="Pass12345", full_name="Referrer2")
        referred = User.objects.create_user(
            phone_number="+2348018880008", password="Pass12345", full_name="Referred2",
            referred_by=referrer, is_phone_verified=False,
        )
        record, raw_code = OTPVerification.generate(referred.phone_number, OTPPurpose.REGISTRATION)

        response = api_client.post(
            reverse("accounts:verify-otp"),
            {"phone_number": referred.phone_number, "code": raw_code, "purpose": "registration"},
        )
        assert response.status_code == status.HTTP_200_OK

        reward = AirtimeTransaction.objects.filter(
            recipient=referrer, purpose=AirtimePurpose.REFERRAL_REWARD
        ).first()
        assert reward is not None
        assert reward.sender is None

    def test_no_reward_when_no_referrer(self, api_client):
        user = User.objects.create_user(
            phone_number="+2348018880009", password="Pass12345", full_name="Solo", is_phone_verified=False
        )
        record, raw_code = OTPVerification.generate(user.phone_number, OTPPurpose.REGISTRATION)

        response = api_client.post(
            reverse("accounts:verify-otp"),
            {"phone_number": user.phone_number, "code": raw_code, "purpose": "registration"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert AirtimeTransaction.objects.filter(purpose=AirtimePurpose.REFERRAL_REWARD).count() == 0

    def test_reward_not_duplicated_on_repeated_registration_verify_calls(self, api_client, settings):
        settings.AFRICASTALKING["DEMO_MODE"] = True
        referrer = User.objects.create_user(phone_number="+2348018880010", password="Pass12345", full_name="Referrer3")
        referred = User.objects.create_user(
            phone_number="+2348018880011", password="Pass12345", full_name="Referred3",
            referred_by=referrer, is_phone_verified=True,  # already verified — second verify shouldn't re-reward
        )
        record, raw_code = OTPVerification.generate(referred.phone_number, OTPPurpose.REGISTRATION)

        api_client.post(
            reverse("accounts:verify-otp"),
            {"phone_number": referred.phone_number, "code": raw_code, "purpose": "registration"},
        )
        assert AirtimeTransaction.objects.filter(purpose=AirtimePurpose.REFERRAL_REWARD).count() == 0

    def test_referral_code_visible_on_me_endpoint(self, api_client):
        user = User.objects.create_user(phone_number="+2348018880012", password="Pass12345", full_name="Visible")
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("accounts:me"))
        assert response.data["referral_code"] == user.referral_code
