from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserProfileSerializer
from .serializers_core import TaskSerializer, UserModeSettingsSerializer, MatchSerializer, QuestSerializer, ChatSerializer, MessageSerializer
from .models import Task, UserModeSettings, Match, Quests, Chat, Message
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone


from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)
from .serializers_core import PreferenceSerializer, UserPreferenceSerializer
from .models import Preference, UserPreference

User = get_user_model()

@extend_schema_view(
    get=extend_schema(responses=UserProfileSerializer),
    put=extend_schema(request=UserProfileSerializer, responses=UserProfileSerializer),
)
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(responses=TaskSerializer(many=True)),
    post=extend_schema(request=TaskSerializer, responses=TaskSerializer),
)
class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(
    get=extend_schema(responses=TaskSerializer),
    put=extend_schema(request=TaskSerializer, responses=TaskSerializer),
    delete=extend_schema(responses=OpenApiResponse(description="No content", response=None)),
)
class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(responses=UserModeSettingsSerializer),
    put=extend_schema(request=UserModeSettingsSerializer, responses=UserModeSettingsSerializer),
)
class UserModeSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        settings_obj, _ = UserModeSettings.objects.get_or_create(user=request.user)
        serializer = UserModeSettingsSerializer(settings_obj)
        return Response(serializer.data)

    def put(self, request):
        settings_obj, _ = UserModeSettings.objects.get_or_create(user=request.user)
        serializer = UserModeSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(responses=MatchSerializer(many=True)),
    post=extend_schema(request=MatchSerializer, responses=MatchSerializer),
)
class MatchListCreateView(generics.ListCreateAPIView):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(Q(user1=user) | Q(user2=user)).order_by("-matched_at")

    def perform_create(self, serializer):
        serializer.save(user1=self.request.user)


@extend_schema_view(
    get=extend_schema(responses=MatchSerializer),
    put=extend_schema(request=MatchSerializer, responses=MatchSerializer),
    delete=extend_schema(responses=OpenApiResponse(description="No content", response=None)),
)
class MatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(Q(user1=user) | Q(user2=user))

    def destroy(self, request, *args, **kwargs):
        """Hard delete the Match row. Ownership is enforced by get_queryset()."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, *args, **kwargs):
        """Update the Match instance (explicit PUT handler for testing)."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(
    request=None,
    responses=MatchSerializer,
    description="Create or return a Match between authenticated user and user_id (PUT).",
)
class MatchWithUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, user_id):
        # cannot match with self
        if request.user.id == user_id:
            return Response({"detail": "cannot match with yourself"}, status=status.HTTP_400_BAD_REQUEST)
        # ensure target user exists
        target = get_object_or_404(User, pk=user_id)
        # check existing match in either order
        match = Match.objects.filter(
            (Q(user1=request.user) & Q(user2=target)) | (Q(user1=target) & Q(user2=request.user))
        ).first()
        if match:
            serializer = MatchSerializer(match)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # create new match with request.user as user1
        match = Match.objects.create(user1=request.user, user2=target, matched_at=timezone.now())
        serializer = MatchSerializer(match)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(responses=QuestSerializer(many=True)),
    post=extend_schema(request=QuestSerializer, responses=QuestSerializer),
)
class QuestListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # only quests for matches where user is participant
        return Quests.objects.filter(Q(match__user1=user) | Q(match__user2=user)).order_by("-quest_date")

    def perform_create(self, serializer):
        # trust provided match; could add extra validation here
        serializer.save()


@extend_schema_view(
    get=extend_schema(responses=QuestSerializer),
    put=extend_schema(request=QuestSerializer, responses=QuestSerializer),
    delete=extend_schema(responses=OpenApiResponse(description="No content", response=None)),
)
class QuestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Quests.objects.filter(Q(match__user1=user) | Q(match__user2=user))

    def destroy(self, request, *args, **kwargs):
        """Hard delete the Quest row. Ownership is enforced by get_queryset()."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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


@extend_schema_view(
    get=extend_schema(responses=PreferenceSerializer(many=True)),
    post=extend_schema(request=PreferenceSerializer, responses=PreferenceSerializer),
)
class PreferenceListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PreferenceSerializer

    def get_queryset(self):
        return Preference.objects.all().order_by("name")


@extend_schema_view(
    get=extend_schema(responses=UserPreferenceSerializer(many=True)),
    post=extend_schema(request=UserPreferenceSerializer, responses=UserPreferenceSerializer),
)
class UserPreferenceListCreateView(generics.ListCreateAPIView):
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user).select_related("preference").order_by("created_at")

    def perform_create(self, serializer):
        pref = serializer.validated_data.get("preference")
        UserPreference.objects.get_or_create(user=self.request.user, preference=pref)


class UserPreferenceDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPreferenceSerializer

    def get_object(self):
        pref_id = self.kwargs.get("pref_id")
        return get_object_or_404(UserPreference, user=self.request.user, preference_id=pref_id)
