from django.contrib import admin

from .models import VoiceVerification


@admin.register(VoiceVerification)
class VoiceVerificationAdmin(admin.ModelAdmin):
    list_display = ["user", "status", "is_demo", "created_at"]
    list_filter = ["status", "is_demo"]
    readonly_fields = [f.name for f in VoiceVerification._meta.fields]

    def has_add_permission(self, request):
        return False
