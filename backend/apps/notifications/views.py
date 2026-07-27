from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, SMSPurpose
from .serializers import NotificationSerializer, SendSMSNotificationSerializer
from .services import send_sms_notification


class SendSMSNotificationView(APIView):
    """
    POST /api/v1/notifications/sms/ — send an arbitrary SMS notification.
    Intended for internal/admin/test use — regular notifications are
    triggered automatically by the matching/messaging/communities flows.
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = SendSMSNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = send_sms_notification(
            serializer.validated_data["phone_number"],
            serializer.validated_data["message"],
            purpose=serializer.validated_data.get("purpose", SMSPurpose.OTHER),
        )
        return Response({"id": record.id, "status": record.status}, status=status.HTTP_201_CREATED)


class NotificationListView(generics.ListAPIView):
    """GET /api/v1/notifications/ — the authenticated user's in-app notification feed."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
