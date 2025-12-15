"""
Preference Models
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Preference(models.Model):
    """
    Lookup table for user interests and preferences.
    Examples: "Books", "Gym", "Coffee", "Hiking", etc.
    """
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        verbose_name = _("preference")
        verbose_name_plural = _("preferences")
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserPreference(models.Model):
    """
    Many-to-Many relationship between Users and Preferences.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences"
    )
    preference = models.ForeignKey(
        Preference,
        on_delete=models.CASCADE,
        related_name="users"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "preference")
        verbose_name = _("user preference")
        verbose_name_plural = _("user preferences")
        ordering = ["created_at"]

    def __str__(self):
        return f"UserPreference user={self.user_id} pref={self.preference_id}"
