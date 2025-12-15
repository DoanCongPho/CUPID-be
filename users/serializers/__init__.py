"""
Users App Serializers Package

Organized serializer structure:
- auth.py: RegisterSerializer, LoginSerializer, TokenResponseSerializer
- profile.py: UserProfileSerializer
- task.py: TaskSerializer, UserModeSettingsSerializer
- match.py: MatchSerializer, QuestSerializer
- chat.py: ChatSerializer, MessageSerializer
- preference.py: PreferenceSerializer, UserPreferenceSerializer
"""

# Authentication serializers
from .auth import (
    RegisterSerializer,
    LoginSerializer,
    TokenResponseSerializer,
)

# Profile serializers
from .profile import UserProfileSerializer

# Task and settings serializers
from .task import (
    TaskSerializer,
    UserModeSettingsSerializer,
)

# Match serializers
from .match import (
    MatchSerializer,
    QuestSerializer,
)

# Chat serializers
from .chat import (
    ChatSerializer,
    MessageSerializer,
)

# Preference serializers
from .preference import (
    PreferenceSerializer,
    UserPreferenceSerializer,
)


# Export all serializers for backward compatibility
__all__ = [
    # Authentication
    "RegisterSerializer",
    "LoginSerializer",
    "TokenResponseSerializer",
    # Profile
    "UserProfileSerializer",
    # Task & Settings
    "TaskSerializer",
    "UserModeSettingsSerializer",
    # Match
    "MatchSerializer",
    "QuestSerializer",
    # Chat
    "ChatSerializer",
    "MessageSerializer",
    # Preference
    "PreferenceSerializer",
    "UserPreferenceSerializer",
]
