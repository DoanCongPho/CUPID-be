"""
Token Authentication Models
"""
import secrets
import hashlib
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ExpiringToken(models.Model):
    """
    Token-based authentication with expiration and revocation support.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auth_tokens"
    )
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    revoked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("expiring token")
        verbose_name_plural = _("expiring tokens")

    def __str__(self):
        return f"Token for {self.user_id} (revoked={self.revoked})"

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash token using SHA256"""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def generate_token_for_user(cls, user, days_valid: int = 365, name: str = ""):
        """
        Generate a new token for a user.
        Returns: (plaintext_token, token_object)
        """
        plaintext = secrets.token_urlsafe(48)
        key_hash = cls._hash_token(plaintext)
        expires = timezone.now() + timedelta(days=days_valid)
        obj = cls.objects.create(
            user=user,
            key_hash=key_hash,
            expires_at=expires,
            name=name
        )
        return plaintext, obj

    @classmethod
    def verify_token(cls, token_plaintext: str):
        """Verify a token and return token object if valid."""
        key_hash = cls._hash_token(token_plaintext)
        now = timezone.now()
        try:
            tok = cls.objects.get(key_hash=key_hash, revoked=False)
        except cls.DoesNotExist:
            return None
        if tok.expires_at < now:
            return None
        return tok

    def revoke(self):
        """Revoke this token"""
        self.revoked = True
        self.save(update_fields=["revoked"])
