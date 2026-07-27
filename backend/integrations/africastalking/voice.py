"""
Voice integration.

IMPORTANT — scope note (per project instruction to never invent
undocumented Africa's Talking behaviour): this build does not have
verified access to an Africa's Talking Voice sandbox, so the *live*
outbound-call flow ("Africa's Talking calls user -> user confirms ->
webhook -> profile verified") is intentionally NOT implemented here
with fabricated endpoint/payload assumptions.

What IS implemented: a demo-mode simulation of the same user-facing
flow, so the product story and UI can be demoed end-to-end. Before
enabling AT_DEMO_MODE=false for Voice specifically, confirm the current
Voice API shape (call initiation endpoint, XML/webhook callback format)
against Africa's Talking's official docs and fill in `_send_live` below
accordingly — do not assume the SMS/Airtime patterns transfer directly.
"""
import logging
import uuid

from .client import is_demo_mode

logger = logging.getLogger("connectlite")


class VoiceResult:
    def __init__(self, success: bool, provider_call_id: str, is_demo: bool):
        self.success = success
        self.provider_call_id = provider_call_id
        self.is_demo = is_demo


class VoiceService:
    @staticmethod
    def start_verification_call(phone_number: str) -> VoiceResult:
        if is_demo_mode():
            return VoiceService._send_demo(phone_number)
        return VoiceService._send_live(phone_number)

    @staticmethod
    def _send_demo(phone_number: str) -> VoiceResult:
        fake_id = f"DEMO-VOICE-{uuid.uuid4().hex[:12]}"
        logger.info(
            "[DEMO MODE] Would place a verification call to %s — no real call placed. provider_call_id=%s",
            VoiceService._mask(phone_number),
            fake_id,
        )
        return VoiceResult(success=True, provider_call_id=fake_id, is_demo=True)

    @staticmethod
    def _send_live(phone_number: str) -> VoiceResult:
        raise NotImplementedError(
            "Live Africa's Talking Voice integration is not implemented in this build. "
            "Verify the current Voice API against official AT documentation before adding it — "
            "see this module's docstring."
        )

    @staticmethod
    def _mask(phone_number: str) -> str:
        if len(phone_number) <= 4:
            return "****"
        return f"{phone_number[:-4]}****"
