"""
API v1 root router — all phases now wired up.

Phase 1: accounts (auth + OTP)
Phase 2: profiles, matching
Phase 3: notifications, communities, messaging + SMS webhooks
Phase 4: ussd
Phase 5: airtime
Phase 6: voice (demo-mode only — see apps/voice and integrations/africastalking/voice.py)

NOTE: webhook_urlpatterns lists are included as (patterns, app_name)
tuples rather than bare lists — passing a bare list to include() does
NOT apply the module's app_name, which would silently break
reverse("notifications:sms-incoming-webhook") etc. This was caught
during the Phase 9 QA pass; see docs/development.md for the write-up.
"""
from django.urls import include, path

from apps.notifications.urls import webhook_urlpatterns as sms_webhook_urlpatterns
from apps.voice.urls import webhook_urlpatterns as voice_webhook_urlpatterns

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.profiles.urls")),
    path("", include("apps.matching.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.communities.urls")),
    path("", include("apps.messaging.urls")),
    path("", include("apps.ussd.urls")),
    path("", include("apps.airtime.urls")),
    path("", include("apps.voice.urls")),
    path("", include((sms_webhook_urlpatterns, "notifications"))),
    path("", include((voice_webhook_urlpatterns, "voice"))),
]
