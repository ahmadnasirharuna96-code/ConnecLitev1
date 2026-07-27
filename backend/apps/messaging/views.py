from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation
from .serializers import ConversationSerializer, MessageSerializer, SendMessageSerializer
from .services import send_message

User = get_user_model()


class ConversationListView(APIView):
    """GET /api/v1/conversations/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.for_user(request.user).order_by("-updated_at")
        return Response(ConversationSerializer(conversations, many=True, context={"request": request}).data)


class MessageListCreateView(APIView):
    """
    GET /api/v1/conversations/<conversation_id>/messages/
    POST /api/v1/messages/  body: {"to_user_id": ..., "content": ...}
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation.for_user(request.user), id=conversation_id)
        messages = conversation.messages.order_by("created_at")
        return Response(MessageSerializer(messages, many=True).data)


class SendMessageView(APIView):
    """POST /api/v1/messages/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        to_user = get_object_or_404(User, id=serializer.validated_data["to_user_id"])

        if to_user.id == request.user.id:
            return Response({"error": "You cannot message yourself."}, status=status.HTTP_400_BAD_REQUEST)

        message = send_message(request.user, to_user, serializer.validated_data["content"])
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
