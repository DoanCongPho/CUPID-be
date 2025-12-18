"""
Profile views for the users app.
"""
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema_view, extend_schema

from ..serializers.profile import UserProfileSerializer
from ..models import Match

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


@extend_schema(
    responses=UserProfileSerializer
)
class UserPublicProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        
        match = Match.objects.filter(
            (Q(user1=request.user) & Q(user2=target_user)) |
            (Q(user1=target_user) & Q(user2=request.user))
        ).exists()
        
        if not match:
            return Response(
                {"detail": "You must be matched with this user to view their profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get and return the profile
        profile = get_object_or_404(target_user.profile)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
