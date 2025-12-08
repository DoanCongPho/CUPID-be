from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserProfileSerializer
from .serializers_core import TaskSerializer, UserModeSettingsSerializer
from .models import Task, UserModeSettings

# drf-spectacular schema helpers
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)

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
