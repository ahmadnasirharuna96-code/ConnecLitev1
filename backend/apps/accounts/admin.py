from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import OTPVerification, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-created_at"]
    list_display = ["phone_number", "full_name", "email", "is_phone_verified", "registration_channel", "is_active"]
    list_filter = ["is_phone_verified", "registration_channel", "gender", "is_active", "is_staff"]
    search_fields = ["phone_number", "full_name", "email"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("id", "phone_number", "password")}),
        ("Personal info", {"fields": ("full_name", "email", "date_of_birth", "gender", "location")}),
        ("Registration", {"fields": ("registration_channel", "is_phone_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("phone_number", "full_name", "password1", "password2")}),
    )


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    # Deliberately excludes code_hash from list_display / never shows plaintext (it isn't stored).
    list_display = ["phone_number", "purpose", "attempts", "max_attempts", "is_used", "expires_at", "created_at"]
    list_filter = ["purpose", "is_used"]
    search_fields = ["phone_number"]
    readonly_fields = [f.name for f in OTPVerification._meta.fields]

    def has_add_permission(self, request):
        return False
