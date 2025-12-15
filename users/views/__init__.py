"""
Users App Views Package

Organized view structure:
- auth.py: RegisterView, LoginView, LogoutView, TokenListView
- profile.py: ProfileView
- task.py: TaskListCreateView, TaskDetailView, UserModeSettingsView
- match.py: MatchListCreateView, MatchDetailView, MatchWithUserView, QuestListCreateView, QuestDetailView
- chat.py: ChatListCreateView, ChatDetailView, MessageListCreateView, MessageDetailView
- preference.py: PreferenceListCreateView, UserPreferenceListCreateView, UserPreferenceDestroyView
"""

# Authentication views
from .auth import (
    RegisterView,
    LoginView,
    LogoutView,
    TokenListView,
)

# Profile views
from .profile import ProfileView

# Task and settings views
from .task import (
    TaskListCreateView,
    TaskDetailView,
    UserModeSettingsView,
)

# Match and quest views
from .match import (
    MatchListCreateView,
    MatchDetailView,
    MatchWithUserView,
    QuestListCreateView,
    QuestDetailView,
)

# Chat and message views
from .chat import (
    ChatListCreateView,
    ChatDetailView,
    MessageListCreateView,
    MessageDetailView,
)

# Preference views
from .preference import (
    PreferenceListCreateView,
    UserPreferenceListCreateView,
    UserPreferenceDestroyView,
)


# Export all views for backward compatibility
__all__ = [
    # Authentication
    "RegisterView",
    "LoginView",
    "LogoutView",
    "TokenListView",
    # Profile
    "ProfileView",
    # Task & Settings
    "TaskListCreateView",
    "TaskDetailView",
    "UserModeSettingsView",
    # Match & Quest
    "MatchListCreateView",
    "MatchDetailView",
    "MatchWithUserView",
    "QuestListCreateView",
    "QuestDetailView",
    # Chat & Message
    "ChatListCreateView",
    "ChatDetailView",
    "MessageListCreateView",
    "MessageDetailView",
    # Preference
    "PreferenceListCreateView",
    "UserPreferenceListCreateView",
    "UserPreferenceDestroyView",
]
