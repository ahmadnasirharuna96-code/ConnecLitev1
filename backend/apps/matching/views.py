import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ConnectionRequest, Match
from .scoring import compatibility_score
from .serializers import (
    ConnectionRequestSerializer,
    DiscoverUserSerializer,
    MatchSerializer,
    RespondConnectionRequestSerializer,
    SendConnectionRequestSerializer,
)
from .services import DuplicateRequestError, respond_to_connection_request, send_connection_request

logger = logging.getLogger("connectlite")
User = get_user_model()

DISCOVER_LIMIT = 50


class DiscoverView(APIView):
    """
    GET /api/v1/discover/ — candidate users ranked by compatibility score.

    Deviation from the literal endpoint list in the brief: the brief only
    specifies GET /matches/ and POST /matches/request/. A dedicated
    discovery endpoint is added because "discover compatible users" is an
    explicit feature requirement and doesn't fit the semantics of
    /matches/ (which represents *confirmed* matches, not candidates).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        already_connected_ids = set(
            ConnectionRequest.objects.filter(Q(from_user=user) | Q(to_user=user)).values_list(
                "from_user_id", "to_user_id"
            )
        )
        exclude_ids = {user.id}
        for a, b in already_connected_ids:
            exclude_ids.add(a)
            exclude_ids.add(b)

        candidates = (
            User.objects.filter(is_active=True)
            .exclude(id__in=exclude_ids)
            .select_related("profile")
        )

        scored = []
        for candidate in candidates:
            if not hasattr(candidate, "profile"):
                continue
            score = compatibility_score(user, candidate)
            scored.append({"user": candidate, "compatibility_score": score})

        scored.sort(key=lambda item: item["compatibility_score"], reverse=True)
        scored = scored[:DISCOVER_LIMIT]

        return Response(DiscoverUserSerializer(scored, many=True).data)


class SendConnectionRequestView(APIView):
    """POST /api/v1/matches/request/ — send a connection request to another user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendConnectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        to_user = get_object_or_404(User, id=serializer.validated_data["to_user_id"])

        try:
            connection_request, match = send_connection_request(request.user, to_user)
        except DuplicateRequestError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        except ValidationError as exc:
            return Response({"error": exc.message}, status=status.HTTP_400_BAD_REQUEST)

        payload = {"request": ConnectionRequestSerializer(connection_request).data}
        if match:
            payload["match"] = MatchSerializer(match, context={"request": request}).data
            payload["message"] = "It's a match! You both connected."
        else:
            payload["message"] = "Connection request sent."

        return Response(payload, status=status.HTTP_201_CREATED)


class ConnectionRequestListView(APIView):
    """GET /api/v1/connections/?direction=incoming|outgoing (default: both)"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        direction = request.query_params.get("direction")
        user = request.user

        if direction == "incoming":
            qs = ConnectionRequest.objects.filter(to_user=user)
        elif direction == "outgoing":
            qs = ConnectionRequest.objects.filter(from_user=user)
        else:
            qs = ConnectionRequest.objects.filter(Q(from_user=user) | Q(to_user=user))

        qs = qs.select_related("from_user__profile", "to_user__profile").order_by("-created_at")
        return Response(ConnectionRequestSerializer(qs, many=True).data)


class RespondConnectionRequestView(APIView):
    """POST /api/v1/connections/<id>/respond/  body: {"action": "accept" | "reject"}"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        connection_request = get_object_or_404(ConnectionRequest, id=pk)
        serializer = RespondConnectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        accept = serializer.validated_data["action"] == "accept"

        try:
            match = respond_to_connection_request(connection_request, request.user, accept)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        payload = {"request": ConnectionRequestSerializer(connection_request).data}
        if match:
            payload["match"] = MatchSerializer(match, context={"request": request}).data
        return Response(payload)


class MatchListView(APIView):
    """GET /api/v1/matches/ — confirmed matches for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        matches = Match.for_user(request.user).select_related(
            "user_low__profile", "user_high__profile"
        ).order_by("-created_at")
        return Response(MatchSerializer(matches, many=True, context={"request": request}).data)
