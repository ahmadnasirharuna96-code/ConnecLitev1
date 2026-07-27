from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AirtimeTransaction
from .serializers import AirtimeTransactionSerializer, GiftAirtimeSerializer
from .services import AirtimeValidationError, DuplicateTransactionError, gift_airtime


class GiftAirtimeView(APIView):
    """POST /api/v1/airtime/gift/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GiftAirtimeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transaction = gift_airtime(
                sender=request.user,
                recipient_phone=serializer.validated_data["recipient_phone"],
                amount=serializer.validated_data["amount"],
                idempotency_key=serializer.validated_data.get("idempotency_key"),
            )
        except AirtimeValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except DuplicateTransactionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(AirtimeTransactionSerializer(transaction).data, status=status.HTTP_201_CREATED)


class AirtimeTransactionListView(APIView):
    """GET /api/v1/airtime/transactions/ — transactions sent or received by the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = AirtimeTransaction.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).order_by("-created_at")
        return Response(AirtimeTransactionSerializer(transactions, many=True).data)
