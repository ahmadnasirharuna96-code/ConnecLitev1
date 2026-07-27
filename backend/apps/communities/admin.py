from django.contrib import admin

from .models import Community, CommunityMembership


class MembershipInline(admin.TabularInline):
    model = CommunityMembership
    extra = 0


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "is_verified", "member_count", "created_by"]
    search_fields = ["name"]
    inlines = [MembershipInline]
