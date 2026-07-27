from django.contrib import admin

from .models import USSDSession


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = ["session_id", "phone_number", "current_state", "is_active", "updated_at"]
    search_fields = ["phone_number", "session_id"]
    readonly_fields = [f.name for f in USSDSession._meta.fields]

    def has_add_permission(self, request):
        return False
