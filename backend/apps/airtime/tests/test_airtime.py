import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.airtime.models import AirtimePurpose, AirtimeStatus, AirtimeTransaction
from apps.airtime.services import (
    AirtimeValidationError,
    DuplicateTransactionError,
    community_reward,
    gift_airtime,
    reward_referral,
)
from apps.communities.models import Community, CommunityMembership, MembershipRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


def make_user(phone, name):
    return User.objects.create_user(phone_number=phone, password="Pass12345", full_name=name, is_phone_verified=True)


@pytest.mark.django_db
class TestGiftAirtimeService:
    def test_successful_gift_in_demo_mode(self, settings):
        settings.AFRICASTALKING["DEMO_MODE"] = True
        sender = make_user("+2348016660001", "Sender")
        recipient = make_user("+2348016660002", "Recipient")

        txn = gift_airtime(sender, recipient.phone_number, 100)
        assert txn.status == AirtimeStatus.SUCCESS
        assert txn.provider_transaction_id.startswith("DEMO-AT-")
        assert txn.purpose == AirtimePurpose.GIFT

    def test_self_gift_rejected(self):
        sender = make_user("+2348016660003", "Sender")
        with pytest.raises(AirtimeValidationError):
            gift_airtime(sender, sender.phone_number, 100)

    def test_gift_to_unregistered_number_rejected(self):
        sender = make_user("+2348016660004", "Sender")
        with pytest.raises(AirtimeValidationError):
            gift_airtime(sender, "+2349999999999", 100)

    def test_amount_below_minimum_rejected(self, settings):
        settings.AIRTIME_SETTINGS["MIN_AMOUNT"] = 50.0
        sender = make_user("+2348016660005", "Sender")
        recipient = make_user("+2348016660006", "Recipient")
        with pytest.raises(AirtimeValidationError):
            gift_airtime(sender, recipient.phone_number, 10)

    def test_amount_above_maximum_rejected(self, settings):
        settings.AIRTIME_SETTINGS["MAX_AMOUNT"] = 5000.0
        sender = make_user("+2348016660007", "Sender")
        recipient = make_user("+2348016660008", "Recipient")
        with pytest.raises(AirtimeValidationError):
            gift_airtime(sender, recipient.phone_number, 10000)

    def test_negative_or_zero_amount_rejected(self):
        sender = make_user("+2348016660009", "Sender")
        recipient = make_user("+2348016660010", "Recipient")
        with pytest.raises(AirtimeValidationError):
            gift_airtime(sender, recipient.phone_number, 0)
        with pytest.raises(AirtimeValidationError):
            gift_airtime(sender, recipient.phone_number, -50)

    def test_duplicate_idempotency_key_rejected(self):
        sender = make_user("+2348016660011", "Sender")
        recipient = make_user("+2348016660012", "Recipient")
        gift_airtime(sender, recipient.phone_number, 100, idempotency_key="fixed-key-1")
        with pytest.raises(DuplicateTransactionError):
            gift_airtime(sender, recipient.phone_number, 100, idempotency_key="fixed-key-1")


@pytest.mark.django_db
class TestReferralReward:
    def test_referral_reward_created(self):
        referrer = make_user("+2348016660013", "Referrer")
        referred = make_user("+2348016660014", "Referred")
        txn = reward_referral(referrer, referred)
        assert txn.purpose == AirtimePurpose.REFERRAL_REWARD
        assert txn.recipient == referrer
        assert txn.sender is None

    def test_self_referral_rejected(self):
        user = make_user("+2348016660015", "Solo")
        with pytest.raises(AirtimeValidationError):
            reward_referral(user, user)

    def test_referral_reward_cannot_be_claimed_twice(self):
        referrer = make_user("+2348016660016", "Referrer2")
        referred = make_user("+2348016660017", "Referred2")
        reward_referral(referrer, referred)
        with pytest.raises(DuplicateTransactionError):
            reward_referral(referrer, referred)


@pytest.mark.django_db
class TestCommunityReward:
    def test_non_admin_cannot_reward(self):
        admin = make_user("+2348016660018", "Admin")
        member = make_user("+2348016660019", "Member")
        community = Community.objects.create(name="Test Community", created_by=admin)
        CommunityMembership.objects.create(community=community, user=member, role=MembershipRole.MEMBER)

        with pytest.raises(PermissionError):
            community_reward(member, community, member, 100)  # member trying to act as admin

    def test_admin_can_reward_member(self):
        admin = make_user("+2348016660020", "Admin2")
        member = make_user("+2348016660021", "Member2")
        community = Community.objects.create(name="Test Community 2", created_by=admin)
        CommunityMembership.objects.create(community=community, user=admin, role=MembershipRole.ADMIN)
        CommunityMembership.objects.create(community=community, user=member, role=MembershipRole.MEMBER)

        txn = community_reward(admin, community, member, 100)
        assert txn.status == AirtimeStatus.SUCCESS
        assert txn.purpose == AirtimePurpose.COMMUNITY_REWARD


@pytest.mark.django_db
class TestAirtimeEndpoints:
    def test_gift_endpoint(self, api_client):
        sender = make_user("+2348016660022", "Sender")
        recipient = make_user("+2348016660023", "Recipient")
        api_client.force_authenticate(user=sender)
        response = api_client.post(
            reverse("airtime:gift"), {"recipient_phone": recipient.phone_number, "amount": "100.00"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "success"

    def test_gift_endpoint_rejects_invalid_amount(self, api_client):
        sender = make_user("+2348016660024", "Sender")
        recipient = make_user("+2348016660025", "Recipient")
        api_client.force_authenticate(user=sender)
        response = api_client.post(
            reverse("airtime:gift"), {"recipient_phone": recipient.phone_number, "amount": "-5"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_transaction_list_only_shows_own_transactions(self, api_client):
        sender = make_user("+2348016660026", "Sender")
        recipient = make_user("+2348016660027", "Recipient")
        outsider = make_user("+2348016660028", "Outsider")
        gift_airtime(sender, recipient.phone_number, 100)

        api_client.force_authenticate(user=outsider)
        response = api_client.get(reverse("airtime:transaction-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

        api_client.force_authenticate(user=sender)
        response = api_client.get(reverse("airtime:transaction-list"))
        assert len(response.data) == 1
