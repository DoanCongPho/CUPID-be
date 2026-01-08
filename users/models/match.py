"""
Match and Quest Models
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Match(models.Model):
    """
    Represents a match between two users.
    Each user has their own status for tracking quest completion.
    """
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
    ]

    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="matches_as_user1",
        on_delete=models.CASCADE,
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="matches_as_user2",
        on_delete=models.CASCADE,
    )
    status_user1 = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    status_user2 = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    matched_at = models.DateTimeField(null=True, blank=True)
    user1_rating = models.IntegerField(null=True, blank=True)
    user2_rating = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("match")
        verbose_name_plural = _("matches")
        indexes = [
            models.Index(fields=["matched_at"]),
        ]

    def __str__(self):
        return f"Match {self.pk}: {self.user1_id} <-> {self.user2_id} ({self.status})"


class Quests(models.Model):
    """
    Quest activities associated with matches.
    Both users must complete the quest to get XP rewards.
    """
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
    ]

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="quests",
    )
    location_name = models.CharField(max_length=255, blank=True)
    hint_user1 = models.CharField(max_length=255, blank=True, default="")
    hint_user2 = models.CharField(max_length=255, blank=True, default="")
    activity = models.CharField(max_length=255)
    quest_date = models.DateField()
    location_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True
    )
    location_longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True
    )
    status_user1 = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    status_user2 = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    xp_reward = models.IntegerField(null=True, blank=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("quest")
        verbose_name_plural = _("quests")
        indexes = [
            models.Index(fields=["quest_date"]),
        ]
        unique_together = ('match', 'location_name')

    def __str__(self):
        return f"Quest {self.pk} for match {self.match_id} ({self.status})"
