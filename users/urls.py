"""
Authentication URL Configuration.

URL Design:
- All auth endpoints live under /api/auth/
- RESTful naming: nouns for resources, verbs only for actions (login, logout)
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    ProfileView,
    ChangePasswordView,
    LogoutView,
)
app_name = "users"

urlpatterns = [
    # Registration
    path("register/", RegisterView.as_view(), name="register"),

    # Login — returns access + refresh tokens + user data
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),

    # Token refresh — exchange refresh token for new access token
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # User profile
    path("me/", ProfileView.as_view(), name="profile"),

    # Password management
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    # Logout — blacklists refresh token
    path("logout/", LogoutView.as_view(), name="logout"),
]
