from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import OTPPurpose

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    referred_by_code = serializers.CharField(
        write_only=True, required=False, allow_blank=True, max_length=10,
        help_text="Another user's shareable referral_code, if this signup was referred.",
    )

    class Meta:
        model = User
        fields = [
            "phone_number",
            "email",
            "password",
            "full_name",
            "date_of_birth",
            "gender",
            "location",
            "referred_by_code",
        ]

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        return value

    def validate_referred_by_code(self, value):
        if not value:
            return value
        if not User.objects.filter(referral_code=value.strip().upper()).exists():
            raise serializers.ValidationError("This referral code was not recognized.")
        return value.strip().upper()

    def create(self, validated_data):
        password = validated_data.pop("password")
        referred_by_code = validated_data.pop("referred_by_code", None)

        user = User(**validated_data)
        user.set_password(password)
        user.is_phone_verified = False
        if referred_by_code:
            user.referred_by = User.objects.filter(referral_code=referred_by_code).first()
        user.save()
        return user


class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    purpose = serializers.ChoiceField(choices=OTPPurpose.choices, default=OTPPurpose.REGISTRATION)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=10)
    purpose = serializers.ChoiceField(choices=OTPPurpose.choices, default=OTPPurpose.REGISTRATION)


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "email",
            "full_name",
            "date_of_birth",
            "gender",
            "location",
            "is_phone_verified",
            "registration_channel",
            "referral_code",
            "created_at",
        ]
        read_only_fields = fields
