from django.urls import path

from .views import (
    ConnectionRequestListView,
    DiscoverView,
    MatchListView,
    RespondConnectionRequestView,
    SendConnectionRequestView,
)

app_name = "matching"

urlpatterns = [
    path("discover/", DiscoverView.as_view(), name="discover"),
    path("matches/", MatchListView.as_view(), name="match-list"),
    path("matches/request/", SendConnectionRequestView.as_view(), name="send-request"),
    path("connections/", ConnectionRequestListView.as_view(), name="connection-list"),
    path("connections/<uuid:pk>/respond/", RespondConnectionRequestView.as_view(), name="connection-respond"),
]
