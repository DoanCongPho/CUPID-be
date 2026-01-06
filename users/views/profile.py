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
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from supabase import create_client
import uuid

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


@extend_schema(
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'avatar': {'type': 'string', 'format': 'binary'}
            },
            'required': ['avatar']
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'avatar_url': {'type': 'string', 'format': 'uri'}
            }
        },
        400: {'description': 'No file uploaded.'},
        500: {'description': 'Upload failed.'}
    },
    description="Upload a user avatar to Supabase Storage (bucket: avatars). Accepts a multipart/form-data POST with 'avatar' file field. Updates the user's profile_photo_url with the public URL."
)
class UserAvatarUploadView(APIView):
    """
    API endpoint to upload a user avatar to Supabase Storage (bucket: avatars).
    Accepts a multipart/form-data POST with 'avatar' file field.
    Updates the user's profile_photo_url with the public URL.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get("avatar")
        if not file_obj:
            return Response({"detail": "No file uploaded."}, status=400)

        # Use user id and uuid to avoid filename collision
        filename = f"{uuid.uuid4().hex}_{file_obj.name}"
        # Pass file bytes instead of file object
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        res = supabase.storage.from_("avatars").upload(filename, file_obj.read(), file_options={"content-type": file_obj.content_type, "upsert": "true"})

        if hasattr(res, "error") and res.error:
            return Response({"detail": "Upload failed.", "error": res.error}, status=500)

        public_url = supabase.storage.from_("avatars").get_public_url(filename)
        profile = request.user.profile
        profile.profile_photo_url = public_url
        profile.save()
        return Response({"avatar_url": public_url})
