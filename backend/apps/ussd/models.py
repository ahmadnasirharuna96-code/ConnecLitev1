import uuid

from django.db import models


class USSDSession(models.Model):
    """
    Server-side USSD session state. Africa's Talking sends the full
    accumulated `text` on every request, but we also keep our own
    state/context so multi-step flows (like registration) don't have to
    be re-derived from the raw text path on every hop.
    """

    session_id = models.CharField(max_length=100, primary_key=True)
    phone_number = models.CharField(max_length=20, db_index=True)
    current_state = models.CharField(max_length=50, default="MAIN_MENU")
    context = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ussd_session"

    def __str__(self):
        return f"USSDSession({self.session_id}, {self.current_state})"
