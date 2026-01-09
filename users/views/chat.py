"""
Chat and Message views for the users app.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse

from ..models import Chat, Message
from ..serializers.chat import ChatSerializer, MessageSerializer


@extend_schema_view(
    get=extend_schema(responses=ChatSerializer(many=True)),
    post=extend_schema(request=ChatSerializer, responses=ChatSerializer),
)
class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(Q(match__user1=user) | Q(match__user2=user)).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save()


@extend_schema_view(
    get=extend_schema(responses=ChatSerializer),
    put=extend_schema(request=ChatSerializer, responses=ChatSerializer),
    delete=extend_schema(responses=OpenApiResponse(description="No content", response=None)),
)
class ChatDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(Q(match__user1=user) | Q(match__user2=user))


@extend_schema_view(
    get=extend_schema(responses=MessageSerializer(many=True)),
    post=extend_schema(
        request=MessageSerializer,
        responses=MessageSerializer,
        description="Send a message to a chat. Automatically sets sender from authenticated user.",
    ),
)
class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Only return messages in chats that the authenticated user participates in.
        """
        chat_id = (
            self.kwargs.get("chat_pk")
            or self.request.query_params.get("chat")
        )

        qs = Message.objects.filter(chat_id=chat_id).order_by("sent_at")
        user = self.request.user

        return qs.filter(
            Q(chat__match__user1=user) | Q(chat__match__user2=user)
        )

    def perform_create(self, serializer):
        """
        Validates chat ownership, saves the message, and broadcasts via Channels.
        """
        from rest_framework.exceptions import ValidationError

        chat_id = (
            self.kwargs.get("chat_pk")
        )

        if not chat_id:
            raise ValidationError({"chat": "chat id is required"})

        # Ensure the chat exists AND belongs to the auth user
        chat = get_object_or_404(
            Chat.objects.filter(
                Q(match__user1=self.request.user) |
                Q(match__user2=self.request.user)
            ),
            pk=chat_id
        )

        # Save the message
        msg = serializer.save(sender=self.request.user, chat=chat)

        # Broadcast over WebSocket
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if channel_layer:
                payload = {
                    "id": msg.id,
                    "chat_id": msg.chat_id,
                    "sender": {
                        "id": msg.sender_id,
                        "email": getattr(msg.sender, "email", None),
                    },
                    "content": msg.content,
                    "sent_at": msg.sent_at.isoformat(),
                }

                async_to_sync(channel_layer.group_send)(
                    f"chat_{chat_id}",
                    {"type": "chat.message", "message": payload},
                )
        except Exception:
            pass


@extend_schema_view(
    get=extend_schema(responses=MessageSerializer),
    delete=extend_schema(responses=OpenApiResponse(description="No content", response=None)),
)
class MessageDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(chat__match__user1=user) | Q(chat__match__user2=user))
