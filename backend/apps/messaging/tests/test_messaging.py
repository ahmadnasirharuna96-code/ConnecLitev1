import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import RegistrationChannel
from apps.messaging.models import Conversation, MessageChannel, MessageStatus
from apps.messaging.services import deliver_inbound_sms, send_message

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


def make_user(phone, name, channel=RegistrationChannel.WEB):
    return User.objects.create_user(
        phone_number=phone, password="Pass12345", full_name=name, is_phone_verified=True,
        registration_channel=channel,
    )


@pytest.mark.django_db
class TestSendMessageRouting:
    def test_app_to_app_message_is_delivered_immediately(self):
        a = make_user("+2348013330001", "Smartphone User A")
        b = make_user("+2348013330002", "Smartphone User B")
        message = send_message(a, b, "Hey there!")
        assert message.channel == MessageChannel.APP
        assert message.status == MessageStatus.DELIVERED

    def test_message_to_feature_phone_user_bridges_to_sms(self, settings):
        settings.AFRICASTALKING["DEMO_MODE"] = True
        a = make_user("+2348013330003", "Smartphone User")
        b = make_user("+2348013330004", "Feature Phone User", channel=RegistrationChannel.USSD)
        message = send_message(a, b, "Hello from the app!")
        assert message.channel == MessageChannel.SMS
        assert message.status == MessageStatus.SENT
        assert message.external_sms_id.startswith("DEMO-")

    def test_conversation_is_reused_for_same_pair(self):
        a = make_user("+2348013330005", "A")
        b = make_user("+2348013330006", "B")
        send_message(a, b, "first")
        send_message(b, a, "second")
        assert Conversation.for_user(a).count() == 1


@pytest.mark.django_db
class TestInboundSMSDelivery:
    def test_inbound_sms_routes_into_existing_conversation(self):
        smartphone_user = make_user("+2348013330007", "Smartphone User")
        feature_phone_user = make_user("+2348013330008", "Feature Phone User", channel=RegistrationChannel.USSD)
        send_message(smartphone_user, feature_phone_user, "Hi, are you free this weekend?")

        deliver_inbound_sms("+2348013330008", "Yes! Let's meet up")

        conversation = Conversation.for_user(smartphone_user).first()
        messages = list(conversation.messages.order_by("created_at"))
        assert len(messages) == 2
        assert messages[-1].content == "Yes! Let's meet up"
        assert messages[-1].channel == MessageChannel.SMS

    def test_inbound_sms_from_unregistered_number_is_dropped_safely(self):
        # Should not raise, even though there's no matching user.
        deliver_inbound_sms("+2349999999999", "hello")


@pytest.mark.django_db
class TestMessagingEndpoints:
    def test_send_message_endpoint(self, api_client):
        a = make_user("+2348013330009", "A")
        b = make_user("+2348013330010", "B")
        api_client.force_authenticate(user=a)
        response = api_client.post(reverse("messaging:send-message"), {"to_user_id": str(b.id), "content": "hi"})
        assert response.status_code == status.HTTP_201_CREATED

    def test_cannot_message_self(self, api_client):
        a = make_user("+2348013330011", "A")
        api_client.force_authenticate(user=a)
        response = api_client.post(reverse("messaging:send-message"), {"to_user_id": str(a.id), "content": "hi"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_conversation_list_requires_auth(self, api_client):
        response = api_client.get(reverse("messaging:conversation-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
