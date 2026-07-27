import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.communities.models import Community, CommunityMembership, MembershipRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(phone_number="+2348014440001", password="Pass12345", full_name="Founder")


@pytest.mark.django_db
class TestCommunities:
    def test_create_community_makes_creator_admin(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse("communities:list-create"), {"name": "BUK Students", "category": "university"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        community = Community.objects.get(name="BUK Students")
        membership = CommunityMembership.objects.get(community=community, user=user)
        assert membership.role == MembershipRole.ADMIN

    def test_join_and_leave_community(self, api_client, user, db):
        community = Community.objects.create(name="Kano Developers", created_by=user)
        other = User.objects.create_user(phone_number="+2348014440002", password="Pass12345", full_name="Joiner")
        api_client.force_authenticate(user=other)

        join_response = api_client.post(reverse("communities:join", kwargs={"pk": community.id}))
        assert join_response.status_code == status.HTTP_201_CREATED
        assert CommunityMembership.objects.filter(community=community, user=other).exists()

        leave_response = api_client.post(reverse("communities:leave", kwargs={"pk": community.id}))
        assert leave_response.status_code == status.HTTP_200_OK
        assert not CommunityMembership.objects.filter(community=community, user=other).exists()

    def test_double_join_is_idempotent(self, api_client, user, db):
        community = Community.objects.create(name="Young Entrepreneurs", created_by=user)
        other = User.objects.create_user(phone_number="+2348014440003", password="Pass12345", full_name="Joiner2")
        api_client.force_authenticate(user=other)
        api_client.post(reverse("communities:join", kwargs={"pk": community.id}))
        response = api_client.post(reverse("communities:join", kwargs={"pk": community.id}))
        assert response.status_code == status.HTTP_200_OK
        assert CommunityMembership.objects.filter(community=community, user=other).count() == 1

    def test_list_members(self, api_client, user, db):
        community = Community.objects.create(name="Tech Community", created_by=user)
        CommunityMembership.objects.create(community=community, user=user, role=MembershipRole.ADMIN)
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("communities:members", kwargs={"pk": community.id}))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
