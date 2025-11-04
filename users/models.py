from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    def __str__(self):
        return self.email if self.email else self.username


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    indirect_teaser = models.CharField(max_length=255, blank=True)

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