"""
Airtime service layer — enforces every security requirement from the
project brief in one place: server-side amount validation, self-reward
prevention, duplicate/replay prevention via idempotency keys, and a
durable PENDING/SUCCESS/FAILED ledger with provider transaction IDs.
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .models import AirtimePurpose, AirtimeStatus, AirtimeTransaction

User = get_user_model()


class AirtimeValidationError(Exception):
    pass


class DuplicateTransactionError(Exception):
    pass


def _validate_amount(amount: float) -> Decimal:
    min_amount = settings.AIRTIME_SETTINGS["MIN_AMOUNT"]
    max_amount = settings.AIRTIME_SETTINGS["MAX_AMOUNT"]
    try:
        amount_decimal = Decimal(str(amount))
    except Exception as exc:  # noqa: BLE001
        raise AirtimeValidationError("Invalid amount.") from exc

    if amount_decimal <= 0:
        raise AirtimeValidationError("Amount must be greater than zero.")
    if amount_decimal < Decimal(str(min_amount)):
        raise AirtimeValidationError(f"Minimum airtime gift is {min_amount}.")
    if amount_decimal > Decimal(str(max_amount)):
        raise AirtimeValidationError(f"Maximum airtime gift is {max_amount}.")
    return amount_decimal


def _execute_transaction(sender, recipient, amount_decimal: Decimal, purpose: str, idempotency_key: str) -> AirtimeTransaction:
    from integrations.africastalking.airtime import AirtimeService
    from integrations.africastalking.exceptions import AirtimeTransactionError

    try:
        transaction = AirtimeTransaction.objects.create(
            sender=sender,
            recipient=recipient,
            amount=amount_decimal,
            currency=settings.AIRTIME_SETTINGS["CURRENCY"],
            purpose=purpose,
            idempotency_key=idempotency_key,
            status=AirtimeStatus.PENDING,
        )
    except IntegrityError as exc:
        raise DuplicateTransactionError("This transaction has already been submitted.") from exc

    try:
        result = AirtimeService.send(recipient.phone_number, float(amount_decimal))
        transaction.status = AirtimeStatus.SUCCESS if result.success else AirtimeStatus.FAILED
        transaction.provider_transaction_id = result.provider_transaction_id
        if not result.success:
            transaction.failure_reason = (result.error or "Provider declined the transaction")[:255]
        transaction.save(update_fields=["status", "provider_transaction_id", "failure_reason", "updated_at"])
    except AirtimeTransactionError as exc:
        transaction.status = AirtimeStatus.FAILED
        transaction.failure_reason = str(exc)[:255]
        transaction.save(update_fields=["status", "failure_reason", "updated_at"])

    return transaction


def gift_airtime(sender, recipient_phone: str, amount: float, idempotency_key: str | None = None) -> AirtimeTransaction:
    """User-to-user airtime gifting — the MUST-HAVE demo flow."""
    if sender.phone_number == recipient_phone:
        raise AirtimeValidationError("You cannot gift airtime to yourself.")

    recipient = User.objects.filter(phone_number=recipient_phone, is_active=True).first()
    if not recipient:
        raise AirtimeValidationError("Recipient is not a registered ConnectLite user.")

    amount_decimal = _validate_amount(amount)
    idempotency_key = idempotency_key or f"gift:{sender.id}:{recipient.id}:{uuid.uuid4().hex}"

    return _execute_transaction(sender, recipient, amount_decimal, AirtimePurpose.GIFT, idempotency_key)


def reward_referral(referrer, referred_user) -> AirtimeTransaction:
    """
    System-initiated referral reward. Not yet wired into registration
    (no referral-code field exists on the registration flow — deferred,
    per hackathon-scope guidance, rather than shipped half-built). The
    idempotency key ties the reward to the specific (referrer, referred)
    pair, so a given referral can only ever be rewarded once.
    """
    if referrer.id == referred_user.id:
        raise AirtimeValidationError("Self-referral is not allowed.")

    amount_decimal = _validate_amount(settings.AIRTIME_SETTINGS["REFERRAL_REWARD_AMOUNT"])
    idempotency_key = f"referral:{referrer.id}:{referred_user.id}"

    return _execute_transaction(None, referrer, amount_decimal, AirtimePurpose.REFERRAL_REWARD, idempotency_key)


def community_reward(admin_user, community, recipient, amount: float) -> AirtimeTransaction:
    """Community administrators rewarding an eligible member."""
    from apps.communities.models import CommunityMembership, MembershipRole

    is_admin = CommunityMembership.objects.filter(
        community=community, user=admin_user, role=MembershipRole.ADMIN
    ).exists()
    if not is_admin:
        raise PermissionError("Only community admins can issue community rewards.")

    is_member = CommunityMembership.objects.filter(community=community, user=recipient).exists()
    if not is_member:
        raise AirtimeValidationError("Recipient is not a member of this community.")

    amount_decimal = _validate_amount(amount)
    idempotency_key = f"community:{community.id}:{admin_user.id}:{recipient.id}:{uuid.uuid4().hex}"

    return _execute_transaction(admin_user, recipient, amount_decimal, AirtimePurpose.COMMUNITY_REWARD, idempotency_key)
