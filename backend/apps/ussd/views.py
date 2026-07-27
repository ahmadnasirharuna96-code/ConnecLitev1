from django.http import HttpResponse
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .services import handle_ussd_request


class USSDWebhookView(APIView):
    """
    POST /api/v1/webhooks/ussd/

    Africa's Talking USSD gateway posts: sessionId, phoneNumber,
    serviceCode, text. Response must be plain text starting with
    "CON " (continue) or "END " (terminate) — NOT JSON — per AT's USSD
    contract, so we return a plain django.http.HttpResponse (bypassing
    DRF's JSON-rendering Response) rather than wrapping the text in JSON.
    """

    permission_classes = [AllowAny]
    parser_classes = [FormParser, JSONParser]
    authentication_classes = []

    def post(self, request):
        session_id = request.data.get("sessionId", "")
        phone_number = request.data.get("phoneNumber", "")
        service_code = request.data.get("serviceCode", "")
        text = request.data.get("text", "")

        if not session_id or not phone_number:
            response_text = "END Invalid session."
        else:
            response_text = handle_ussd_request(session_id, phone_number, text, service_code)

        return HttpResponse(response_text, content_type="text/plain")
