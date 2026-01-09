"""
Task Models
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Task(models.Model):
    """
    User tasks and to-do items.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="tasks",
        on_delete=models.CASCADE
    )
    description = models.TextField()
    scheduled_start_time = models.DateTimeField(null=True, blank=True)
    scheduled_end_time = models.DateTimeField(null=True, blank=True)
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("task")
        verbose_name_plural = _("tasks")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task: {self.description[:50]}"
