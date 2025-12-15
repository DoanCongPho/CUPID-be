"""
Preference Serializers
Serializers for Preference and UserPreference models
"""
from rest_framework import serializers
from users.models import Preference, UserPreference


class PreferenceSerializer(serializers.ModelSerializer):
    """Serializer for Preference model"""

    class Meta:
        model = Preference
        fields = ["id", "name"]
        read_only_fields = ["id"]


class UserPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for UserPreference model.
    Handles the many-to-many relationship between User and Preference.
    """
    preference = PreferenceSerializer(read_only=True)
    preference_id = serializers.PrimaryKeyRelatedField(
        source="preference",
        queryset=Preference.objects.all(),
        write_only=True
    )

    class Meta:
        model = UserPreference
        fields = ["preference", "preference_id", "created_at"]
        read_only_fields = ["created_at"]
