from django.contrib import admin

from .models import Interest, Profile, UserInterest


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ["name", "category"]
    search_fields = ["name"]


class UserInterestInline(admin.TabularInline):
    model = UserInterest
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "occupation", "verification_status"]
    search_fields = ["user__full_name", "user__phone_number"]
    inlines = [UserInterestInline]
