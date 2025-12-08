from rest_framework import serializers
from .models import UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "full_name",
            "nickname",
            "teaser_description",
            "profile_photo_url",
            "verification_video_url",
            "is_verified",
            "total_xp",
            "date_of_birth",
            "home_latitude",
            "home_longitude",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "username", "email", "total_xp", "is_verified"]