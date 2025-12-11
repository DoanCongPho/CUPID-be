from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile, UserModeSettings, Match, Chat

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_related_objects(sender, instance, created, **kwargs):
    """
    Tự động tạo UserProfile và UserModeSettings khi User mới được tạo.
    Dùng get_or_create để tránh lỗi Duplicate nếu signal chạy 2 lần.
    """

    UserProfile.objects.get_or_create(user=instance)

    if created:
        UserModeSettings.objects.get_or_create(user=instance)

@receiver(post_save, sender=Match)
def create_chat_for_match(sender, instance, created, **kwargs):
    """Create a Chat row automatically when a new Match is created."""
    if created:
        Chat.objects.get_or_create(match=instance)

