from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Task, UserModeSettings, Match, Quests, Chat, Message
from .models import Preference, UserPreference

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = UserModeSettings
        fields = [
            "ghost_mode_enabled",
            "daily_reminders_enabled",
            "location_sharing_enabled",
            "spotmatch_notifications_enabled",
        ]


class MatchSerializer(serializers.ModelSerializer):
    # user1 is read-only (will be set to request.user on create)
    user1 = serializers.SerializerMethodField(read_only=True)
    # client provides user2 by id when creating a match
    user2_id = serializers.PrimaryKeyRelatedField(source="user2", queryset=User.objects.all(), write_only=True)
    user2 = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "user1",
            "user2",
            "user2_id",
            "status",
            "matched_at",
            "user1_rating",
            "user2_rating",
        ]
        read_only_fields = ["id", "user1", "user2", "matched_at"]

    def get_user_representation(self, user):
        if not user:
            return None
        return {"id": user.id, "email": getattr(user, "email", None)}

    def get_user1(self, obj):
        return self.get_user_representation(obj.user1)

    def get_user2(self, obj):
        return self.get_user_representation(obj.user2)


# add Quest serializer
class QuestSerializer(serializers.ModelSerializer):
    # client provides match by id when creating
    match_id = serializers.PrimaryKeyRelatedField(source="match", queryset=Match.objects.all(), write_only=True)
    match = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Quests
        fields = [
            "id",
            "match",
            "match_id",
            "location_name",
            "activity",
            "location_latitude",
            "location_longitude",
            "quest_date",
            "hint_user1",
            "hint_user2",
            "status",
            "xp_reward",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "match", "created_at", "updated_at"]

    def get_match(self, obj):
        if not obj.match:
            return None
        return {"id": obj.match.id, "user1_id": obj.match.user1_id, "user2_id": obj.match.user2_id}


class ChatSerializer(serializers.ModelSerializer):
    match_id = serializers.PrimaryKeyRelatedField(source="match", queryset=Match.objects.all(), write_only=True)
    match = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Chat
        fields = ["id", "match", "match_id", "status", "created_at"]
        read_only_fields = ["id", "match", "created_at"]

    def get_match(self, obj):
        if not obj.match:
            return None
        return {"id": obj.match.id, "user1_id": obj.match.user1_id, "user2_id": obj.match.user2_id}


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "chat", "sender", "content", "sent_at"]
        read_only_fields = ["id", "sender", "sent_at", "chat"]

    def get_sender(self, obj):
        if not obj.sender:
            return None
        return {"id": obj.sender.id, "email": getattr(obj.sender, "email", None)}


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ["id", "name"]
        read_only_fields = ["id"]


class UserPreferenceSerializer(serializers.ModelSerializer):
    preference = PreferenceSerializer(read_only=True)
    preference_id = serializers.PrimaryKeyRelatedField(source="preference", queryset=Preference.objects.all(), write_only=True)

    class Meta:
        model = UserPreference
        fields = ["preference", "preference_id", "created_at"]
        read_only_fields = ["created_at"]
