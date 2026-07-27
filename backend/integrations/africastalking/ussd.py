"""
USSD response helpers.

Unlike SMS/Airtime, Africa's Talking USSD has no "send" API to wrap —
AT calls *our* webhook and expects a plain-text response prefixed with
CON (continue session, show more menu) or END (terminate session).
This module just centralizes that response formatting so app code never
hand-rolls the prefix.
"""


def continue_session(message: str) -> str:
    return f"CON {message}"


def end_session(message: str) -> str:
    return f"END {message}"
