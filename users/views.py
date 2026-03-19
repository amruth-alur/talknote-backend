"""
Authentication Views for TalkNote.

Architecture:
- APIView (not ViewSet) for auth endpoints — auth operations are actions,
  not CRUD on a resource, so ViewSets would be semantically misleading.
- Each view has a single responsibility (SOLID: Single Responsibility Principle).

Error Handling Strategy:
- Serializer validation errors are returned automatically by DRF (400).
- Unexpected errors are caught, logged, and return generic 500 (never leak internals).
"""
import logging
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
)

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Creates a new user account and returns JWT tokens.

    Returns tokens immediately so the frontend can redirect
    to the dashboard without requiring a separate login step.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # Generate tokens for immediate login after registration
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Account created successfully.",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Authenticates user with email + password, returns JWT tokens + user data.
    """
    serializer_class = CustomTokenObtainPairSerializer


class ProfileView(APIView):
    """
    GET  /api/auth/me/  — Retrieve current user profile.
    PUT  /api/auth/me/  — Update current user profile (first_name, last_name).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        # Only allow updating safe fields
        allowed_fields = {"first_name", "last_name"}
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        if not update_data:
            return Response(
                {"error": "No valid fields to update. Allowed: first_name, last_name."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for field, value in update_data.items():
            setattr(user, field, value)
        user.save(update_fields=list(update_data.keys()) + ["updated_at"])

        logger.info("Profile updated for user: %s", user.email)
        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Allows authenticated users to change their password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password updated successfully."},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token so it can't be reused.

    Trade-off: This requires SimpleJWT's token blacklist app.
    Without it, JWTs remain valid until expiry. We blacklist
    the refresh token to prevent new access tokens from being issued.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("User logged out: %s", request.user.email)
            return Response(
                {"message": "Logged out successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.warning("Logout failed for user %s: %s", request.user.email, str(e))
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
