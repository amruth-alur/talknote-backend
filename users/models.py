"""
Custom User Model for TalkNote.

Design Decision: We use AbstractUser (not AbstractBaseUser) to inherit
Django's built-in auth fields (is_staff, is_active, groups, permissions)
while overriding the identifier to be email instead of username.

This provides the best balance between customization and compatibility
with Django's admin, permissions system, and third-party packages.
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class User(AbstractUser):
    """
    Custom User model — email is the primary identifier.
    Username field is removed entirely.
    """
    # Remove username field
    username = None

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as the login field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Email & password are required by default

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Returns the user's full name, or email if no name is set."""
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email
