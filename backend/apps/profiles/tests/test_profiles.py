import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.profiles.models import Interest, Profile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        phone_number="+2348011110000", password="Pass12345", full_name="Amina Yusuf", is_phone_verified=True
    )


@pytest.mark.django_db
class TestProfileAutoCreation:
    def test_profile_created_automatically_on_user_creation(self, user):
        assert Profile.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestMyProfileEndpoint:
    def test_requires_authentication(self, api_client):
        response = api_client.get(reverse("profiles:my-profile"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_own_profile(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("profiles:my-profile"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Amina Yusuf"

    def test_update_bio_and_location(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            reverse("profiles:my-profile"), {"bio": "Loves hiking", "location": "Kano"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.location == "Kano"
        assert user.profile.bio == "Loves hiking"

    def test_update_interests(self, api_client, user):
        hiking = Interest.objects.create(name="Hiking")
        coding = Interest.objects.create(name="Coding")
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            reverse("profiles:my-profile"),
            {"interest_ids": [str(hiking.id), str(coding.id)]},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert user.profile.interests.count() == 2


@pytest.mark.django_db
class TestPublicProfileEndpoint:
    def test_public_profile_excludes_private_fields(self, api_client, user, db):
        other = User.objects.create_user(
            phone_number="+2348022223333", password="Pass12345", full_name="Other User"
        )
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("profiles:public-profile", kwargs={"user_id": other.id}))
        assert response.status_code == status.HTTP_200_OK
        assert "phone_number" not in response.data
        assert "email" not in response.data


@pytest.mark.django_db
class TestInterestCatalog:
    def test_list_interests(self, api_client, user):
        Interest.objects.create(name="Reading")
        Interest.objects.create(name="Football")
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("profiles:interest-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
