"""
Chat and Message Serializers
Serializers for Chat and Message models
"""
from rest_framework import serializers
from users.models import Chat, Message, Match


class ChatSerializer(serializers.ModelSerializer):
    """
    Serializer for Chat model.
    Client provides match_id when creating a chat.
    """
    match_id = serializers.PrimaryKeyRelatedField(
        source="match",
        queryset=Match.objects.all(),
        write_only=True
    )
    match = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Chat
        fields = ["id", "match", "match_id", "status", "created_at"]
        read_only_fields = ["id", "match", "created_at"]

    def get_match(self, obj):
        """Serialize match information"""
        if not obj.match:
            return None
        return {
            "id": obj.match.id,
            "user1_id": obj.match.user1_id,
            "user2_id": obj.match.user2_id
        }


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.
    Sender is automatically set to request.user on create.
    """
    sender = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "chat", "sender", "content", "sent_at"]
        read_only_fields = ["id", "sender", "sent_at", "chat"]

    def get_sender(self, obj):
        """Serialize sender information"""
        if not obj.sender:
            return None
        return {
            "id": obj.sender.id,
            "email": getattr(obj.sender, "email", None)
        }
