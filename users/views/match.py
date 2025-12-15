"""
Match and Quest views for the users app.
"""
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse

from ..models import Match, Quests
from ..serializers.match import MatchSerializer, QuestSerializer

User = get_user_model()


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
