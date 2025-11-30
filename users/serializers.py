from rest_framework import serializers
from .models import UserProfile, Todo
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "bio",
            "avatar_url",
            "date_of_birth",
            "indirect_teaser",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "username", "email"]

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ['id', 'title', 'description', 'is_completed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
