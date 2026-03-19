"""
Authentication Serializers for TalkNote.

Serializers handle:
1. Input validation (OWASP: Validate all inputs)
2. Data transformation (Clean Architecture: boundary between HTTP and domain)
3. Output formatting (API contract)

Trade-offs:
- We use ModelSerializer for Registration to leverage built-in field validation.
- We customize SimpleJWT's TokenObtainPairSerializer to include user data in
  the login response, avoiding an extra API call from the frontend.
"""
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for user profile data.
    Used in responses — never accepts password input.
    """

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "created_at", "updated_at"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles user registration with proper validation.

    Security:
    - Password is write-only (never returned in responses)
    - Django's password validators are applied (min length, common passwords, etc.)
    - Email is normalized and checked for uniqueness at DB level
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm", "first_name", "last_name"]

    def validate_email(self, value):
        """Normalize email to lowercase for consistent lookups."""
        return value.lower().strip()

    def validate(self, attrs):
        """Cross-field validation: ensure passwords match."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Create user with hashed password. Never store plaintext."""
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        logger.info("New user registered: %s", user.email)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extended JWT login serializer.

    Why customize?
    - Default SimpleJWT only returns access + refresh tokens.
    - We add user profile data so the frontend doesn't need a
      separate /me request after login. Reduces latency by 1 RTT.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to the JWT payload
        token["email"] = user.email
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Append user profile alongside the tokens
        data["user"] = UserSerializer(self.user).data
        logger.info("User logged in: %s", self.user.email)
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """
    Handles password change for authenticated users.
    Requires old password verification (OWASP best practice).
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        logger.info("Password changed for user: %s", user.email)
        return user
