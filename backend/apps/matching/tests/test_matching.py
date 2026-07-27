import datetime

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.matching.models import ConnectionRequest, ConnectionRequestStatus, Match
from apps.matching.scoring import compatibility_score
from apps.matching.services import DuplicateRequestError, send_connection_request
from apps.profiles.models import Interest

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


def make_user(phone, name, location="", dob=None, is_verified=True):
    return User.objects.create_user(
        phone_number=phone,
        password="Pass12345",
        full_name=name,
        location=location,
        date_of_birth=dob,
        is_phone_verified=is_verified,
    )


@pytest.mark.django_db
class TestCompatibilityScoring:
    def test_identical_location_and_interests_scores_high(self):
        a = make_user("+2348010000001", "A", location="Kano", dob=datetime.date(1998, 1, 1))
        b = make_user("+2348010000002", "B", location="Kano", dob=datetime.date(1998, 6, 1))
        hiking = Interest.objects.create(name="Hiking")
        a.profile.interests.add(hiking)
        b.profile.interests.add(hiking)

        score = compatibility_score(a, b)
        assert score >= 70  # same location, full interest overlap, near-identical age

    def test_different_location_no_shared_interests_scores_lower(self):
        a = make_user("+2348010000003", "A", location="Kano", dob=datetime.date(1990, 1, 1))
        b = make_user("+2348010000004", "B", location="Lagos", dob=datetime.date(2001, 1, 1))
        Interest.objects.create(name="Hiking")  # a has none, b has none — neutral interest score
        score_a_b = compatibility_score(a, b)

        c = make_user("+2348010000005", "C", location="Kano", dob=datetime.date(1990, 6, 1))
        score_a_c = compatibility_score(a, c)

        assert score_a_c > score_a_b

    def test_score_bounded_0_to_100(self):
        a = make_user("+2348010000006", "A")
        b = make_user("+2348010000007", "B")
        score = compatibility_score(a, b)
        assert 0 <= score <= 100

    def test_weights_are_configurable(self, settings):
        a = make_user("+2348010000008", "A", location="Abuja")
        b = make_user("+2348010000009", "B", location="Abuja")

        settings.MATCHING_WEIGHTS = {"location": 1.0, "interests": 0.0, "age": 0.0, "community": 0.0}
        score = compatibility_score(a, b)
        assert score == 100  # same location, location fully weighted


@pytest.mark.django_db
class TestConnectionRequestService:
    def test_send_request_creates_pending_request(self):
        a = make_user("+2348010000010", "A")
        b = make_user("+2348010000011", "B")
        request_obj, match = send_connection_request(a, b)
        assert request_obj.status == ConnectionRequestStatus.PENDING
        assert match is None

    def test_duplicate_request_raises(self):
        a = make_user("+2348010000012", "A")
        b = make_user("+2348010000013", "B")
        send_connection_request(a, b)
        with pytest.raises(DuplicateRequestError):
            send_connection_request(a, b)

    def test_mutual_request_creates_instant_match(self):
        a = make_user("+2348010000014", "A")
        b = make_user("+2348010000015", "B")
        send_connection_request(a, b)  # A -> B pending
        request_obj, match = send_connection_request(b, a)  # B -> A closes the loop

        assert match is not None
        assert ConnectionRequest.objects.get(from_user=a, to_user=b).status == ConnectionRequestStatus.ACCEPTED
        assert ConnectionRequest.objects.get(from_user=b, to_user=a).status == ConnectionRequestStatus.ACCEPTED
        assert Match.for_user(a).count() == 1
        assert Match.for_user(b).count() == 1


@pytest.mark.django_db
class TestMatchingEndpoints:
    def test_discover_excludes_self(self, api_client):
        a = make_user("+2348010000020", "A")
        api_client.force_authenticate(user=a)
        response = api_client.get(reverse("matching:discover"))
        assert response.status_code == status.HTTP_200_OK
        ids = [item["profile"]["id"] for item in response.data]
        assert str(a.id) not in ids

    def test_discover_ranks_by_compatibility(self, api_client):
        a = make_user("+2348010000021", "A", location="Jos")
        make_user("+2348010000022", "B", location="Jos")
        make_user("+2348010000023", "C", location="Enugu")
        api_client.force_authenticate(user=a)
        response = api_client.get(reverse("matching:discover"))
        scores = [item["compatibility_score"] for item in response.data]
        assert scores == sorted(scores, reverse=True)

    def test_send_request_endpoint(self, api_client):
        a = make_user("+2348010000024", "A")
        b = make_user("+2348010000025", "B")
        api_client.force_authenticate(user=a)
        response = api_client.post(reverse("matching:send-request"), {"to_user_id": str(b.id)}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["request"]["status"] == "pending"

    def test_send_request_to_self_rejected(self, api_client):
        a = make_user("+2348010000026", "A")
        api_client.force_authenticate(user=a)
        response = api_client.post(reverse("matching:send-request"), {"to_user_id": str(a.id)}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_respond_accept_creates_match(self, api_client):
        a = make_user("+2348010000027", "A")
        b = make_user("+2348010000028", "B")
        send_connection_request(a, b)
        req = ConnectionRequest.objects.get(from_user=a, to_user=b)

        api_client.force_authenticate(user=b)
        response = api_client.post(
            reverse("matching:connection-respond", kwargs={"pk": req.id}), {"action": "accept"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "match" in response.data

    def test_respond_forbidden_for_non_recipient(self, api_client):
        a = make_user("+2348010000029", "A")
        b = make_user("+2348010000030", "B")
        send_connection_request(a, b)
        req = ConnectionRequest.objects.get(from_user=a, to_user=b)

        api_client.force_authenticate(user=a)  # sender, not recipient
        response = api_client.post(
            reverse("matching:connection-respond", kwargs={"pk": req.id}), {"action": "accept"}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_match_list_returns_confirmed_matches(self, api_client):
        a = make_user("+2348010000031", "A")
        b = make_user("+2348010000032", "B")
        send_connection_request(a, b)
        req = ConnectionRequest.objects.get(from_user=a, to_user=b)
        api_client.force_authenticate(user=b)
        api_client.post(reverse("matching:connection-respond", kwargs={"pk": req.id}), {"action": "accept"}, format="json")

        response = api_client.get(reverse("matching:match-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
