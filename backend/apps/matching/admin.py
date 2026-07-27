from django.contrib import admin

from .models import ConnectionRequest, Match


@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ["from_user", "to_user", "status", "compatibility_score_snapshot", "created_at"]
    list_filter = ["status"]
    search_fields = ["from_user__full_name", "to_user__full_name"]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ["user_low", "user_high", "compatibility_score", "created_at"]
    search_fields = ["user_low__full_name", "user_high__full_name"]
