from django.contrib import admin

from .models import AirtimeTransaction


@admin.register(AirtimeTransaction)
class AirtimeTransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "sender", "recipient", "amount", "currency", "purpose", "status", "created_at"]
    list_filter = ["purpose", "status", "currency"]
    search_fields = ["sender__full_name", "recipient__full_name", "provider_transaction_id"]
    readonly_fields = [f.name for f in AirtimeTransaction._meta.fields]

    def has_add_permission(self, request):
        return False
