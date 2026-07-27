from django.urls import path

from .views import StartVoiceVerificationView, VoiceWebhookView

app_name = "voice"

urlpatterns = [
    path("voice/verification/start/", StartVoiceVerificationView.as_view(), name="start-verification"),
]

webhook_urlpatterns = [
    path("webhooks/voice/", VoiceWebhookView.as_view(), name="voice-webhook"),
]
