"""
Task and Settings Serializers
Serializers for Task and UserModeSettings models
"""
from rest_framework import serializers
from users.models import Task, UserModeSettings


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""

    class Meta:
        model = Task
        fields = [
            "id",
            "description",
            "scheduled_start_time",
            "scheduled_end_time",
            "is_free",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserModeSettingsSerializer(serializers.ModelSerializer):
    """Serializer for UserModeSettings model"""

    class Meta:
        model = UserModeSettings
        fields = [
            "ghost_mode_enabled",
            "daily_reminders_enabled",
            "location_sharing_enabled",
            "spotmatch_notifications_enabled",
        ]
