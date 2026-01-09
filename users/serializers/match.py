"""
Match and Quest Serializers
Serializers for Match and Quests models
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Match, Quests

User = get_user_model()


class MatchSerializer(serializers.ModelSerializer):
    """
    Serializer for Match model.
    user1 is automatically set to request.user on create.
    """
    # user1 is read-only (will be set to request.user on create)
    user1 = serializers.SerializerMethodField(read_only=True)
    # client provides user2 by id when creating a match
    user2_id = serializers.PrimaryKeyRelatedField(
        source="user2",
        queryset=User.objects.all(),
        write_only=True
    )
    user2 = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "user1",
            "user2",
            "user2_id",
            "status_user1",
            "status_user2",
            "matched_at",
            "user1_rating",
            "user2_rating",
        ]
        read_only_fields = ["id", "user1", "user2", "matched_at"]

    def get_user_representation(self, user):
        """Helper method to serialize user information"""
        if not user:
            return None
        return {
            "id": user.id,
            "email": getattr(user, "email", None)
        }

    def get_user1(self, obj):
        """Serialize user1"""
        return self.get_user_representation(obj.user1)

    def get_user2(self, obj):
        """Serialize user2"""
        return self.get_user_representation(obj.user2)


class QuestSerializer(serializers.ModelSerializer):
    """
    Serializer for Quests model.
    Client provides match_id when creating a quest.
    """
    # client provides match by id when creating
    match_id = serializers.PrimaryKeyRelatedField(
        source="match",
        queryset=Match.objects.all(),
        write_only=True
    )
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
            "hint_user1",
            "hint_user2",
            "quest_date",
            "status_user1",
            "status_user2",
            "xp_reward",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "match", "created_at", "updated_at"]

    def get_match(self, obj):
        """Serialize match information"""
        if not obj.match:
            return None
        return {
            "id": obj.match.id,
            "user1_id": obj.match.user1_id,
            "user2_id": obj.match.user2_id
        }
