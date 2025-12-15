"""
Preference views for the users app.
"""
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse

from ..models import Preference, UserPreference
from ..serializers.preference import PreferenceSerializer, UserPreferenceSerializer


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
