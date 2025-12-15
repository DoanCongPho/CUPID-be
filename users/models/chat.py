"""
Chat and Message Models
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Chat(models.Model):
    """
    Chat conversation between matched users.
    Note: Import Match model using string reference to avoid circular import
    """
    STATUS_ACTIVE = "active"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_CLOSED, "Closed"),
    ]

    match = models.OneToOneField(
        "Match",  # String reference to avoid circular import
        on_delete=models.CASCADE,
        related_name="chat",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("chat")
        verbose_name_plural = _("chats")
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Chat {self.pk} for match {self.match_id} ({self.status})"


class Message(models.Model):
    """
    Individual message in a chat.
    """
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")
        ordering = ["sent_at"]

    def __str__(self):
        return f"Message {self.pk} in chat {self.chat_id} by user {self.sender_id}"
