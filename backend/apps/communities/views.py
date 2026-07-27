from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Community, CommunityMembership, MembershipRole
from .serializers import CommunityMemberSerializer, CommunitySerializer


class CommunityListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/communities/"""

    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        community = serializer.save(created_by=self.request.user)
        CommunityMembership.objects.create(community=community, user=self.request.user, role=MembershipRole.ADMIN)


class CommunityDetailView(generics.RetrieveAPIView):
    """GET /api/v1/communities/<id>/"""

    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    permission_classes = [permissions.IsAuthenticated]


class JoinCommunityView(APIView):
    """POST /api/v1/communities/<id>/join/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        community = get_object_or_404(Community, id=pk)
        _, created = CommunityMembership.objects.get_or_create(community=community, user=request.user)
        if not created:
            return Response({"message": "Already a member."}, status=status.HTTP_200_OK)
        return Response({"message": f"Joined {community.name}."}, status=status.HTTP_201_CREATED)


class LeaveCommunityView(APIView):
    """POST /api/v1/communities/<id>/leave/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        community = get_object_or_404(Community, id=pk)
        deleted, _ = CommunityMembership.objects.filter(community=community, user=request.user).delete()
        if not deleted:
            return Response({"error": "You are not a member of this community."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": f"Left {community.name}."})


class CommunityMembersView(generics.ListAPIView):
    """GET /api/v1/communities/<id>/members/"""

    serializer_class = CommunityMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CommunityMembership.objects.filter(community_id=self.kwargs["pk"]).select_related("user")
