from django.urls import path

from .views import (
    CommunityDetailView,
    CommunityListCreateView,
    CommunityMembersView,
    JoinCommunityView,
    LeaveCommunityView,
)

app_name = "communities"

urlpatterns = [
    path("communities/", CommunityListCreateView.as_view(), name="list-create"),
    path("communities/<uuid:pk>/", CommunityDetailView.as_view(), name="detail"),
    path("communities/<uuid:pk>/join/", JoinCommunityView.as_view(), name="join"),
    path("communities/<uuid:pk>/leave/", LeaveCommunityView.as_view(), name="leave"),
    path("communities/<uuid:pk>/members/", CommunityMembersView.as_view(), name="members"),
]
