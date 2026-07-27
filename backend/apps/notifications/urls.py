from django.urls import path

from .views import NotificationListView, SendSMSNotificationView
from .webhook_views import SMSDeliveryWebhookView, SMSIncomingWebhookView

app_name = "notifications"

urlpatterns = [
    path("notifications/sms/", SendSMSNotificationView.as_view(), name="send-sms"),
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
]

webhook_urlpatterns = [
    path("webhooks/africastalking/sms/incoming/", SMSIncomingWebhookView.as_view(), name="sms-incoming-webhook"),
    path("webhooks/africastalking/sms/delivery/", SMSDeliveryWebhookView.as_view(), name="sms-delivery-webhook"),
]
