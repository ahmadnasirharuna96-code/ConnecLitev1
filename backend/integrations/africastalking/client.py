"""
Shared Africa's Talking SDK client wrapper.

Single place that initializes the `africastalking` SDK with credentials
from settings. Every integration submodule (sms.py, airtime.py, voice.py)
goes through this — nothing in the app imports the SDK directly, and
nothing outside `integrations/africastalking/` ever sees raw AT
credentials or the SDK object itself.

In AT_DEMO_MODE, `get_sdk()` is never called by the service classes —
they short-circuit to local mock behaviour instead. This module still
supports being initialized for when demo mode is switched off.
"""
import logging

from django.conf import settings

logger = logging.getLogger("connectlite")

_sdk_initialized = False


def is_demo_mode() -> bool:
    return bool(settings.AFRICASTALKING["DEMO_MODE"])


def get_sdk():
    """
    Lazily initializes and returns the africastalking SDK module.
    Only called when AT_DEMO_MODE=false. Raises clearly if credentials
    are missing rather than silently failing.
    """
    global _sdk_initialized
    import africastalking

    username = settings.AFRICASTALKING["USERNAME"]
    api_key = settings.AFRICASTALKING["API_KEY"]

    if not api_key:
        raise RuntimeError(
            "AT_API_KEY is not set. Set AT_DEMO_MODE=true for local/demo use, "
            "or provide real Africa's Talking sandbox/production credentials."
        )

    if not _sdk_initialized:
        africastalking.initialize(username, api_key)
        _sdk_initialized = True
        logger.info("Africa's Talking SDK initialized (environment=%s)", settings.AFRICASTALKING["ENVIRONMENT"])

    return africastalking
