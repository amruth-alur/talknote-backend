"""
Authentication Tests for TalkNote.

Testing Strategy:
- Unit tests for serializer validation logic.
- Integration tests for full API request/response cycles.
- Tests cover: registration, login, profile, password change, logout.
- Each test is isolated — no shared state between tests.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationTests(APITestCase):
    """Test suite for POST /api/auth/register/"""

    url = reverse("users:register")

    def test_register_success(self):
        """Valid registration returns 201 with tokens and user data."""
        data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertEqual(response.data["user"]["email"], "test@example.com")
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_register_password_mismatch(self):
        """Mismatched passwords return 400."""
        data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass456!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        """Weak password (too short/common) returns 400."""
        data = {
            "email": "test@example.com",
            "password": "123",
            "password_confirm": "123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """Duplicate email returns 400."""
        User.objects.create_user(email="taken@example.com", password="StrongPass123!")
        data = {
            "email": "taken@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_email_normalized(self):
        """Email with mixed case is normalized to lowercase."""
        data = {
            "email": "  TEST@EXAMPLE.COM  ",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["email"], "test@example.com")

    def test_register_missing_email(self):
        """Missing email returns 400."""
        data = {
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """Test suite for POST /api/auth/login/"""

    url = reverse("users:login")

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
            first_name="Test",
        )

    def test_login_success(self):
        """Valid credentials return tokens and user data."""
        data = {"email": "user@example.com", "password": "StrongPass123!"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "user@example.com")

    def test_login_wrong_password(self):
        """Wrong password returns 401."""
        data = {"email": "user@example.com", "password": "WrongPass"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Non-existent email returns 401."""
        data = {"email": "nobody@example.com", "password": "StrongPass123!"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileTests(APITestCase):
    """Test suite for GET/PUT /api/auth/me/"""

    url = reverse("users:profile")

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
            first_name="Original",
            last_name="Name",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """Authenticated user can retrieve their profile."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "user@example.com")
        self.assertEqual(response.data["first_name"], "Original")

    def test_get_profile_unauthenticated(self):
        """Unauthenticated request returns 401."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        """Authenticated user can update allowed fields."""
        data = {"first_name": "Updated", "last_name": "Person"}
        response = self.client.put(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")
        self.assertEqual(response.data["last_name"], "Person")

    def test_update_profile_cannot_change_email(self):
        """Email field is read-only and should not be updatable via profile."""
        data = {"email": "hacker@evil.com"}
        response = self.client.put(self.url, data, format="json")
        # Should reject — no valid fields to update
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "user@example.com")


class ChangePasswordTests(APITestCase):
    """Test suite for POST /api/auth/change-password/"""

    url = reverse("users:change_password")

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="OldPass123!"
        )
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        """Valid old password + new password returns 200."""
        data = {"old_password": "OldPass123!", "new_password": "NewPass456!"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify the new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))

    def test_change_password_wrong_old(self):
        """Wrong old password returns 400."""
        data = {"old_password": "WrongOldPass!", "new_password": "NewPass456!"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutTests(APITestCase):
    """Test suite for POST /api/auth/logout/"""

    url = reverse("users:logout")

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="StrongPass123!"
        )
        self.client.force_authenticate(user=self.user)
        # Get a real refresh token
        login_response = self.client.post(
            reverse("users:login"),
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.refresh_token = login_response.data["refresh"]

    def test_logout_success(self):
        """Valid refresh token is blacklisted and returns 200."""
        response = self.client.post(
            self.url, {"refresh": self.refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_missing_token(self):
        """Missing refresh token returns 400."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalid_token(self):
        """Invalid refresh token returns 400."""
        response = self.client.post(
            self.url, {"refresh": "invalid-token-string"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserManagerTests(APITestCase):
    """Test suite for the custom UserManager."""

    def test_create_user(self):
        """create_user creates a non-staff, non-superuser account."""
        user = User.objects.create_user(
            email="normal@example.com", password="TestPass123!"
        )
        self.assertEqual(user.email, "normal@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_user_no_email_raises(self):
        """create_user without email raises ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="TestPass123!")

    def test_create_superuser(self):
        """create_superuser creates a staff superuser."""
        admin = User.objects.create_superuser(
            email="admin@example.com", password="AdminPass123!"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
