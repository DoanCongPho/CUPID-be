from rest_framework import serializers
from .models import Task, UserModeSettings


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "description",
            "scheduled_start_time",
            "scheduled_end_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserModeSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModeSettings
        fields = [
            "ghost_mode_enabled",
            "daily_reminders_enabled",
            "location_sharing_enabled",
            "spotmatch_notifications_enabled",
        ]
