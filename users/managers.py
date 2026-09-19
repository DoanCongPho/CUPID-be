"""
Custom manager for the User model.
"""
import re

from django.contrib.auth.models import UserManager as DjangoUserManager


class UserManager(DjangoUserManager):
    """
    Manager for a User model that uses email as its USERNAME_FIELD.

    User declares ``USERNAME_FIELD = "email"`` but still inherits the
    ``username`` field (unique, NOT NULL) from AbstractUser, while Django's
    default manager requires ``username`` as its first positional argument.
    The two disagree.

    This manager bridges the gap: ``create_user(email=..., password=...)``
    works without a username, which is instead derived from the email or
    phone number and de-duplicated.
    """

    def _base_username(self, email=None, phone_number=None):
        """Derive the username stem from an email or phone number."""
        if email:
            base = email.split("@")[0]
        elif phone_number:
            base = phone_number
        else:
            base = "user"

        # AbstractUser.username only allows letters, digits and @ . + - _
        base = re.sub(r"[^\w.@+-]", "", base).strip("._-")
        return base[:140] or "user"

    def generate_username(self, email=None, phone_number=None):
        """Build a unique username, appending a numeric suffix on collision."""
        base = self._base_username(email, phone_number)
        candidate = base
        suffix = 1
        while self.filter(username=candidate).exists():
            suffix += 1
            candidate = f"{base}{suffix}"[:150]
        return candidate

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        if not username:
            username = self.generate_username(email, extra_fields.get("phone_number"))
        return super().create_user(
            username=username, email=email, password=password, **extra_fields
        )

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        if not username:
            username = self.generate_username(email, extra_fields.get("phone_number"))
        return super().create_superuser(
            username=username, email=email, password=password, **extra_fields
        )
