"""
User Profile Serializers
Serializers for UserProfile model
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    Includes username and email from related User model.
    """
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "username",
            "email",
            "full_name",
            "nickname",
            "teaser_description",
            "profile_photo_url",
            "verification_video_url",
            "is_verified",
            "total_xp",
            "is_matched",
            "date_of_birth",
            "home_latitude",
            "home_longitude",
        ]
        read_only_fields = ["user_id", "username", "email", "is_verified", "total_xp"]
