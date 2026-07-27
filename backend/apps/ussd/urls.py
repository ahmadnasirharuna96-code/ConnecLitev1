from django.urls import path

from .views import USSDWebhookView

app_name = "ussd"

urlpatterns = [
    path("webhooks/ussd/", USSDWebhookView.as_view(), name="ussd-webhook"),
]
