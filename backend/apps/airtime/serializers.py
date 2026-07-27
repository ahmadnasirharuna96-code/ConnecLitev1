from rest_framework import serializers

from .models import AirtimeTransaction


class GiftAirtimeSerializer(serializers.Serializer):
    recipient_phone = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    idempotency_key = serializers.CharField(max_length=100, required=False)


class AirtimeTransactionSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True, default=None)
    recipient_name = serializers.CharField(source="recipient.full_name", read_only=True)

    class Meta:
        model = AirtimeTransaction
        fields = [
            "id", "sender_name", "recipient_name", "amount", "currency", "purpose", "status",
            "provider_transaction_id", "failure_reason", "created_at",
        ]
        read_only_fields = fields
