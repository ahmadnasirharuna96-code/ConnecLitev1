import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPPurpose
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    RequestOTPSerializer,
    UserPublicSerializer,
    VerifyOTPSerializer,
)
from .services import OTPThrottleError, request_otp, verify_otp

logger = logging.getLogger("connectlite")
User = get_user_model()


def _issue_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _reward_referrer_safely(user) -> None:
    """
    Rewards user.referred_by with airtime once the *referred* user's
    phone is verified (not at bare registration) — this avoids rewarding
    referrals of numbers that never actually confirm ownership. Reward
    failures must never break the verification/login flow itself.
    """
    if not user.referred_by_id:
        return
    try:
        from apps.airtime.services import AirtimeValidationError, DuplicateTransactionError, reward_referral

        reward_referral(user.referred_by, user)
    except (AirtimeValidationError, DuplicateTransactionError):
        pass  # e.g. reward already claimed for this pair — not an error worth surfacing
    except Exception as exc:  # noqa: BLE001
        logger.warning("Referral reward failed for referrer=%s referred=%s: %s", user.referred_by_id, user.id, exc)


class RegisterView(APIView):
    """POST /api/v1/auth/register/ — smartphone/web registration."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("New web registration for user_id=%s", user.id)
        return Response(
            {
                "message": "Registration successful. Request an OTP to verify your phone number.",
                "user": UserPublicSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class RequestOTPView(APIView):
    """POST /api/v1/auth/request-otp/"""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        purpose = serializer.validated_data["purpose"]

        if purpose == OTPPurpose.LOGIN and not User.objects.filter(phone_number=phone_number).exists():
            # Don't leak account existence details beyond what's necessary.
            return Response({"error": "No account found for this phone number."}, status=status.HTTP_404_NOT_FOUND)

        try:
            request_otp(phone_number, purpose)
        except OTPThrottleError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        return Response({"message": "If this number is valid, a verification code has been sent."})


class VerifyOTPView(APIView):
    """POST /api/v1/auth/verify-otp/"""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        purpose = serializer.validated_data["purpose"]

        if not verify_otp(phone_number, code, purpose):
            return Response({"error": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({"error": "No account found for this phone number."}, status=status.HTTP_404_NOT_FOUND)

        if purpose == OTPPurpose.REGISTRATION and not user.is_phone_verified:
            user.is_phone_verified = True
            user.save(update_fields=["is_phone_verified"])
            _reward_referrer_safely(user)

        tokens = _issue_tokens(user)
        return Response(
            {
                "message": "Verification successful.",
                "user": UserPublicSerializer(user).data,
                "tokens": tokens,
            }
        )


class LoginView(APIView):
    """POST /api/v1/auth/login/ — password-based login."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            user = None

        if user is None or not user.check_password(password):
            return Response({"error": "Invalid phone number or password."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"error": "This account has been deactivated."}, status=status.HTTP_403_FORBIDDEN)

        if not user.is_phone_verified:
            return Response(
                {"error": "Phone number not verified. Please verify via OTP first."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tokens = _issue_tokens(user)
        return Response({"user": UserPublicSerializer(user).data, "tokens": tokens})


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — blacklists the supplied refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"error": "Invalid or already-expired token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Logged out successfully."})


class MeView(APIView):
    """GET /api/v1/auth/me/ — current authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserPublicSerializer(request.user).data)
