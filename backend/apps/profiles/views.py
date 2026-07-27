from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from .models import Interest, Profile
from .serializers import InterestSerializer, ProfileSerializer, PublicProfileSerializer


class MyProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/profile/ — the authenticated user's own profile."""

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class PublicProfileView(generics.RetrieveAPIView):
    """GET /api/v1/profile/<user_id>/ — limited view of another user's profile."""

    serializer_class = PublicProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "user_id"

    def get_object(self):
        return get_object_or_404(Profile, user_id=self.kwargs["user_id"])


class InterestListView(generics.ListAPIView):
    """GET /api/v1/interests/ — the interest catalog users can attach to their profile."""

    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
