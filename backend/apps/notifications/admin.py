from django.contrib import admin

from .models import Notification, SMSMessage, WebhookEvent


@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ["recipient_phone", "purpose", "status", "is_demo", "created_at"]
    list_filter = ["purpose", "status", "is_demo"]
    search_fields = ["recipient_phone", "provider_message_id"]
    readonly_fields = [f.name for f in SMSMessage._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ["source", "provider_event_id", "processed", "received_at"]
    list_filter = ["source", "processed"]
    readonly_fields = [f.name for f in WebhookEvent._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "notification_type", "title", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read"]
