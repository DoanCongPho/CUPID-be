"""
User Profile Models
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="profile",
        on_delete=models.CASCADE,
        primary_key=True
    )
    full_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    nickname = models.CharField(max_length=255, blank=True)
    teaser_description = models.CharField(max_length=255, blank=True)
    profile_photo_url = models.URLField(blank=True)
    verification_video_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    total_xp = models.IntegerField(default=0)
    is_matched = models.BooleanField(default=False)  # Added from remote
    home_latitude = models.FloatField(null=True, blank=True)
    home_longitude = models.FloatField(null=True, blank=True)
    external_id = models.CharField(max_length=255, blank=True, db_index=True)
    is_service_account = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")
        indexes = [
            models.Index(fields=["external_id"]),
        ]

    def __str__(self):
        return f"Profile of {self.user.username}"


class UserModeSettings(models.Model):
    """
    User application settings and preferences.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="settings",
        on_delete=models.CASCADE
    )
    ghost_mode_enabled = models.BooleanField(default=False)
    daily_reminders_enabled = models.BooleanField(default=True)
    location_sharing_enabled = models.BooleanField(default=True)
    spotmatch_notifications_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("user mode settings")
        verbose_name_plural = _("user mode settings")

    def __str__(self):
        return f"Settings for {self.user.username}"
