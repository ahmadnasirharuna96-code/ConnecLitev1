"""
Airtime integration — the only place that calls Africa's Talking's
Airtime API (or, in demo mode, a local mock).
"""
import logging
import uuid

from .client import get_sdk, is_demo_mode
from .exceptions import AirtimeTransactionError

logger = logging.getLogger("connectlite")


class AirtimeResult:
    def __init__(self, success: bool, provider_transaction_id: str, is_demo: bool, error: str = ""):
        self.success = success
        self.provider_transaction_id = provider_transaction_id
        self.is_demo = is_demo
        self.error = error


class AirtimeService:
    @staticmethod
    def send(phone_number: str, amount: float, currency: str = "NGN") -> AirtimeResult:
        if is_demo_mode():
            return AirtimeService._send_demo(phone_number, amount)
        return AirtimeService._send_live(phone_number, amount, currency)

    @staticmethod
    def _send_demo(phone_number: str, amount: float) -> AirtimeResult:
        fake_id = f"DEMO-AT-{uuid.uuid4().hex[:12]}"
        logger.info(
            "[DEMO MODE] Would send %.2f airtime to %s — no real transaction sent. provider_transaction_id=%s",
            amount,
            AirtimeService._mask(phone_number),
            fake_id,
        )
        return AirtimeResult(success=True, provider_transaction_id=fake_id, is_demo=True)

    @staticmethod
    def _send_live(phone_number: str, amount: float, currency: str) -> AirtimeResult:
        sdk = get_sdk()
        airtime = sdk.Airtime
        try:
            response = airtime.send(
                recipients=[{"phoneNumber": phone_number, "amount": f"{currency} {amount:.2f}"}]
            )
            responses = response.get("responses", [])
            if not responses:
                raise AirtimeTransactionError("Africa's Talking returned no transaction data.")
            result = responses[0]
            success = str(result.get("status", "")).lower() in ("sent", "success")
            return AirtimeResult(
                success=success,
                provider_transaction_id=result.get("requestId", ""),
                is_demo=False,
                error="" if success else result.get("errorMessage", "Unknown error"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Africa's Talking Airtime send failed: %s", exc)
            raise AirtimeTransactionError(str(exc)) from exc

    @staticmethod
    def _mask(phone_number: str) -> str:
        if len(phone_number) <= 4:
            return "****"
        return f"{phone_number[:-4]}****"
