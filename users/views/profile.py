"""
Profile views for the users app.
"""
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema

from ..serializers.profile import UserProfileSerializer


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
