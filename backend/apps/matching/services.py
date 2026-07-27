"""
Service layer for connection requests and matches — keeps the
"mutual-request auto-match" business rule out of views.
"""
from django.core.exceptions import ValidationError

from .models import ConnectionRequest, ConnectionRequestStatus, Match
from .scoring import compatibility_score


class DuplicateRequestError(Exception):
    pass


def send_connection_request(from_user, to_user) -> tuple[ConnectionRequest | None, Match | None]:
    """
    Send a connection request. If the target user already has a pending
    request out to the sender (mutual interest), both requests are
    marked accepted immediately and a Match is created — mirroring how
    "mutual like" works on most matching platforms.

    Returns (connection_request, match) — match is None unless a mutual
    match was formed by this call.
    """
    if from_user.id == to_user.id:
        raise ValidationError("You cannot send a connection request to yourself.")

    if ConnectionRequest.objects.filter(from_user=from_user, to_user=to_user).exists():
        raise DuplicateRequestError("A connection request to this user already exists.")

    score = compatibility_score(from_user, to_user)

    reverse_request = ConnectionRequest.objects.filter(
        from_user=to_user, to_user=from_user, status=ConnectionRequestStatus.PENDING
    ).first()

    if reverse_request:
        reverse_request.status = ConnectionRequestStatus.ACCEPTED
        reverse_request.save(update_fields=["status", "updated_at"])

        forward_request = ConnectionRequest.objects.create(
            from_user=from_user,
            to_user=to_user,
            status=ConnectionRequestStatus.ACCEPTED,
            compatibility_score_snapshot=score,
        )
        match, _ = Match.get_or_create_for(from_user, to_user, score)
        _notify_match_safely(from_user, to_user)
        return forward_request, match

    request = ConnectionRequest.objects.create(
        from_user=from_user, to_user=to_user, compatibility_score_snapshot=score
    )
    _notify_connection_request_safely(to_user, from_user)
    return request, None


def respond_to_connection_request(request_obj: ConnectionRequest, responder, accept: bool) -> Match | None:
    if request_obj.to_user_id != responder.id:
        raise PermissionError("Only the recipient of a connection request may respond to it.")
    if request_obj.status != ConnectionRequestStatus.PENDING:
        raise ValidationError("This connection request has already been responded to.")

    if accept:
        request_obj.status = ConnectionRequestStatus.ACCEPTED
        request_obj.save(update_fields=["status", "updated_at"])
        score = request_obj.compatibility_score_snapshot or compatibility_score(
            request_obj.from_user, request_obj.to_user
        )
        match, _ = Match.get_or_create_for(request_obj.from_user, request_obj.to_user, score)
        _notify_match_safely(request_obj.from_user, request_obj.to_user)
        return match

    request_obj.status = ConnectionRequestStatus.REJECTED
    request_obj.save(update_fields=["status", "updated_at"])
    return None


def _notify_match_safely(user_a, user_b) -> None:
    """Notification failures must never break the core connection/match flow."""
    import logging

    try:
        from apps.notifications.services import notify_match

        notify_match(user_a, user_b)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("connectlite").warning("Match notification failed: %s", exc)


def _notify_connection_request_safely(to_user, from_user) -> None:
    import logging

    try:
        from apps.notifications.services import notify_connection_request

        notify_connection_request(to_user, from_user)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("connectlite").warning("Connection request notification failed: %s", exc)
