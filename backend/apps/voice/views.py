from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import WebhookEvent

from .models import VoiceVerification, VoiceVerificationStatus
from .serializers import VoiceVerificationSerializer


class StartVoiceVerificationView(APIView):
    """
    POST /api/v1/voice/verification/start/

    Demo-mode only in this build (see integrations/africastalking/voice.py).
    In demo mode, the call is simulated and immediately marked verified
    so the product flow can be demoed end-to-end without a live provider.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from integrations.africastalking.voice import VoiceService

        result = VoiceService.start_verification_call(request.user.phone_number)

        record = VoiceVerification.objects.create(
            user=request.user,
            provider_call_id=result.provider_call_id,
            is_demo=result.is_demo,
            status=VoiceVerificationStatus.VERIFIED if result.is_demo else VoiceVerificationStatus.PENDING,
        )

        if result.is_demo:
            request.user.is_phone_verified = True
            request.user.save(update_fields=["is_phone_verified"])

        return Response(VoiceVerificationSerializer(record).data, status=status.HTTP_201_CREATED)


class VoiceWebhookView(APIView):
    """
    POST /api/v1/webhooks/voice/

    Placeholder for the live Africa's Talking Voice callback. Not
    exercised by the demo-mode flow above. Payload handling is left
    unimplemented pending verification of AT's current Voice webhook
    contract (see integrations/africastalking/voice.py) rather than
    guessing at field names.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        provider_event_id = str(request.data.get("sessionId") or request.data.get("callId") or "")
        if not provider_event_id:
            return Response({"error": "missing session/call id"}, status=400)

        WebhookEvent.objects.get_or_create(
            source="voice", provider_event_id=provider_event_id, defaults={"payload": dict(request.data)}
        )
        return Response({"status": "received"})
