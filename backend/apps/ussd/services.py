"""
USSD flow handler.

Africa's Talking USSD is stateless from the app's point of view: every
webhook call carries the FULL accumulated input since the session
started (`text`, segments separated by "*"). We lean into that — the
whole flow is written as a pure function of `text`, with a USSDSession
row kept only for auditing/analytics, not as the source of truth for
navigation state. This keeps the flow simple, restart-safe, and easy to
reason about (no partially-written server-side state to go stale).

UX simplification (documented): unlike the web, USSD registration does
not collect a password — the phone number itself (already authenticated
by the telco/SIM) is the credential, and USSD registrants are
auto-verified. This matches how most USSD-based services work and
keeps the flow short, per the "USSD flow must be short and easy to
navigate" requirement.
"""
import datetime
import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.accounts.models import Gender, RegistrationChannel
from apps.matching.scoring import compatibility_score
from apps.matching.services import DuplicateRequestError, send_connection_request
from apps.messaging.services import send_message

from .models import USSDSession

logger = logging.getLogger("connectlite")
User = get_user_model()

MAX_DISCOVER_RESULTS = 3


def handle_ussd_request(session_id: str, phone_number: str, text: str, service_code: str = "") -> str:
    """Entry point called by the USSD webhook view. Returns a CON/END-prefixed string."""
    from integrations.africastalking.ussd import end_session

    USSDSession.objects.update_or_create(
        session_id=session_id,
        defaults={"phone_number": phone_number, "context": {"last_text": text}},
    )

    try:
        user = User.objects.filter(phone_number=phone_number, is_active=True).first()
        segments = [s for s in text.split("*")] if text else []

        if user is None:
            return _handle_guest_flow(segments, phone_number)
        return _handle_authenticated_flow(segments, user)
    except Exception as exc:  # noqa: BLE001 — a USSD session must never hang or crash on an unhandled error
        logger.error("USSD flow error for session %s: %s", session_id, exc)
        return end_session("Sorry, something went wrong. Please try again later.")


# ---------------------------------------------------------------------
# Guest flow (no ConnectLite account yet)
# ---------------------------------------------------------------------

def _handle_guest_flow(segments: list, phone_number: str) -> str:
    from integrations.africastalking.ussd import continue_session, end_session

    if not segments:
        return continue_session("Welcome to ConnectLite\n1. Register\n2. Help")

    if segments[0] == "2":
        return end_session(_help_text())

    if segments[0] == "1":
        return _handle_registration(segments[1:], phone_number)

    return end_session("Invalid option. Please dial in again.")


def _handle_registration(steps: list, phone_number: str) -> str:
    from integrations.africastalking.ussd import continue_session, end_session

    # Step order: name -> age -> gender -> location -> confirm
    if len(steps) == 0:
        return continue_session("Enter your full name:")

    name = steps[0].strip()
    if not name:
        return end_session("Name cannot be empty. Please dial in again.")

    if len(steps) == 1:
        return continue_session("Enter your age:")

    age_raw = steps[1].strip()
    if not age_raw.isdigit() or not (16 <= int(age_raw) <= 100):
        return end_session("Invalid age. Please dial in again and enter a number between 16 and 100.")

    if len(steps) == 2:
        return continue_session("Select gender:\n1. Male\n2. Female\n3. Other")

    gender_choice = steps[2].strip()
    gender_map = {"1": Gender.MALE, "2": Gender.FEMALE, "3": Gender.OTHER}
    if gender_choice not in gender_map:
        return end_session("Invalid selection. Please dial in again.")

    if len(steps) == 3:
        return continue_session("Enter your location (town/city):")

    location = steps[3].strip()
    if not location:
        return end_session("Location cannot be empty. Please dial in again.")

    if len(steps) == 4:
        return continue_session(
            f"Confirm registration:\nName: {name}\nAge: {age_raw}\nLocation: {location}\n1. Confirm\n2. Cancel"
        )

    confirm_choice = steps[4].strip()
    if confirm_choice == "2":
        return end_session("Registration cancelled.")
    if confirm_choice != "1":
        return end_session("Invalid option. Please dial in again.")

    if User.objects.filter(phone_number=phone_number).exists():
        return end_session("An account with this phone number already exists. Dial in again to access it.")

    approx_dob = datetime.date(datetime.date.today().year - int(age_raw), 1, 1)
    try:
        User.objects.create_user(
            phone_number=phone_number,
            password=None,
            full_name=name,
            gender=gender_map[gender_choice],
            location=location,
            date_of_birth=approx_dob,
            registration_channel=RegistrationChannel.USSD,
            is_phone_verified=True,  # phone already authenticated by the telco/SIM for USSD access
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("USSD registration failed for %s: %s", phone_number, exc)
        return end_session("Registration failed due to a system error. Please try again shortly.")

    return end_session(f"Welcome to ConnectLite, {name}! Dial in again to explore connections.")


# ---------------------------------------------------------------------
# Authenticated flow (existing ConnectLite user)
# ---------------------------------------------------------------------

MAIN_MENU_TEXT = (
    "ConnectLite Menu\n"
    "1. Find Connections\n"
    "2. My Matches\n"
    "3. Communities\n"
    "4. Messages\n"
    "5. My Profile\n"
    "6. Airtime\n"
    "7. Help"
)


def _handle_authenticated_flow(segments: list, user) -> str:
    from integrations.africastalking.ussd import continue_session, end_session

    if not segments:
        return continue_session(MAIN_MENU_TEXT)

    choice, rest = segments[0], segments[1:]

    if choice == "1":
        return _handle_find_connections(rest, user)
    if choice == "2":
        return _handle_my_matches(rest, user)
    if choice == "3":
        return _handle_communities(rest, user)
    if choice == "4":
        return end_session(_messages_summary(user))
    if choice == "5":
        return _handle_profile(rest, user)
    if choice == "6":
        return _handle_airtime(rest, user)
    if choice == "7":
        return end_session(_help_text())

    return end_session("Invalid option. Please dial in again.")


def _discover_candidates(user, limit=MAX_DISCOVER_RESULTS):
    candidates = User.objects.filter(is_active=True).exclude(id=user.id).select_related("profile")
    scored = [(c, compatibility_score(user, c)) for c in candidates if hasattr(c, "profile")]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:limit]


def _handle_find_connections(steps: list, user) -> str:
    from integrations.africastalking.ussd import continue_session, end_session

    candidates = _discover_candidates(user)
    if not candidates:
        return end_session("No connections found right now. Please check back later.")

    if len(steps) == 0:
        lines = ["Top Connections:"]
        for i, (candidate, score) in enumerate(candidates, start=1):
            lines.append(f"{i}. {candidate.full_name.split(' ')[0]} - {score}%")
        return continue_session("\n".join(lines))

    try:
        index = int(steps[0]) - 1
        selected_user, score = candidates[index]
    except (ValueError, IndexError):
        return end_session("Invalid selection. Please dial in again.")

    if len(steps) == 1:
        return continue_session(
            f"{selected_user.full_name.split(' ')[0]} - {score}% compatible\n"
            "1. Send Connection Request\n2. Send SMS\n3. Back"
        )

    action = steps[1]
    if action == "1":
        try:
            _, match = send_connection_request(user, selected_user)
        except DuplicateRequestError:
            return end_session("You've already sent a request to this person.")
        except ValidationError as exc:
            return end_session(str(exc))
        if match:
            return end_session("It's a match! You're now connected.")
        return end_session("Connection request sent.")

    if action == "2":
        if len(steps) == 2:
            return continue_session("Type your message:")
        message_text = steps[2]
        send_message(user, selected_user, message_text)
        return end_session("Message sent.")

    if action == "3":
        return end_session("Dial in again to continue browsing connections.")

    return end_session("Invalid option. Please dial in again.")


def _handle_my_matches(steps: list, user) -> str:
    from integrations.africastalking.ussd import end_session

    from apps.matching.models import Match

    matches = list(Match.for_user(user).select_related("user_low__profile", "user_high__profile")[:5])
    if not matches:
        return end_session("You have no matches yet. Try Find Connections from the main menu.")

    lines = ["Your Matches:"]
    for m in matches:
        other = m.other_user(user)
        lines.append(f"- {other.full_name.split(' ')[0]} ({m.compatibility_score}%)")
    return end_session("\n".join(lines))


def _handle_communities(steps: list, user) -> str:
    from integrations.africastalking.ussd import continue_session, end_session

    from apps.communities.models import Community, CommunityMembership

    communities = list(Community.objects.all()[:5])
    if not communities:
        return end_session("No communities available yet.")

    if len(steps) == 0:
        lines = ["Communities:"]
        for i, c in enumerate(communities, start=1):
            lines.append(f"{i}. {c.name}")
        return continue_session("\n".join(lines))

    try:
        index = int(steps[0]) - 1
        community = communities[index]
    except (ValueError, IndexError):
        return end_session("Invalid selection. Please dial in again.")

    CommunityMembership.objects.get_or_create(community=community, user=user)
    return end_session(f"You have joined {community.name}.")


def _messages_summary(user) -> str:
    from apps.messaging.models import Conversation

    count = Conversation.for_user(user).count()
    if count == 0:
        return "You have no conversations yet."
    return f"You have {count} conversation(s). Reply to any SMS from ConnectLite to keep chatting."


def _handle_profile(steps: list, user) -> str:
    from integrations.africastalking.ussd import continue_session, end_session

    if len(steps) == 0:
        profile = getattr(user, "profile", None)
        age = profile.age if profile else None
        verified = "Verified" if user.is_phone_verified else "Unverified"
        return continue_session(
            f"My Profile\nName: {user.full_name}\nAge: {age or '-'}\nLocation: {user.location or '-'}\n"
            f"Status: {verified}\n1. Update Location\n2. Back"
        )

    if steps[0] == "1":
        if len(steps) == 1:
            return continue_session("Enter new location:")
        new_location = steps[1].strip()
        if not new_location:
            return end_session("Location cannot be empty.")
        user.location = new_location
        user.save(update_fields=["location"])
        return end_session("Location updated.")

    return end_session("Dial in again to return to the main menu.")


def _handle_airtime(steps: list, user) -> str:
    from integrations.africastalking.ussd import continue_session, end_session

    if len(steps) == 0:
        return continue_session("Airtime\n1. Gift Airtime\n2. Back")

    if steps[0] != "1":
        return end_session("Dial in again to return to the main menu.")

    if len(steps) == 1:
        return continue_session("Enter recipient phone number:")
    if len(steps) == 2:
        return continue_session("Enter amount (NGN):")

    recipient_phone = steps[1].strip()
    amount_raw = steps[2].strip()

    if len(steps) == 3:
        return continue_session(f"Send {amount_raw} airtime to {recipient_phone}?\n1. Confirm\n2. Cancel")

    if steps[3] != "1":
        return end_session("Airtime gift cancelled.")

    from apps.airtime.services import AirtimeValidationError, gift_airtime

    try:
        amount = float(amount_raw)
        gift_airtime(sender=user, recipient_phone=recipient_phone, amount=amount)
    except AirtimeValidationError as exc:
        return end_session(str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.error("USSD airtime gift failed: %s", exc)
        return end_session("Airtime gift failed. Please try again later.")

    return end_session(f"Airtime gift of {amount_raw} to {recipient_phone} is being processed.")


def _help_text() -> str:
    return (
        "ConnectLite connects you with people nearby - even without internet.\n"
        "Dial in again anytime to find connections, check matches, join communities, "
        "or gift airtime. For support, contact your ConnectLite community admin."
    )
