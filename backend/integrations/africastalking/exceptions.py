"""Exceptions for the Africa's Talking integration layer."""


class AfricasTalkingError(Exception):
    """Base exception for all Africa's Talking integration failures."""


class SMSDeliveryError(AfricasTalkingError):
    """Raised when an SMS could not be sent or queued by the provider."""


class AirtimeTransactionError(AfricasTalkingError):
    """Raised when an airtime transfer fails at the provider."""


class VoiceCallError(AfricasTalkingError):
    """Raised when initiating/handling a voice call fails."""
