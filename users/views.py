"""
Backward compatibility shim for views.
Imports from the new views package.
"""
from .views import (
    # Profile
    ProfileView,
    # Task & Settings
    TaskListCreateView,
    TaskDetailView,
    UserModeSettingsView,
    # Match & Quest
    MatchListCreateView,
    MatchDetailView,
    MatchWithUserView,
    QuestListCreateView,
    QuestDetailView,
    # Chat & Message
    ChatListCreateView,
    ChatDetailView,
    MessageListCreateView,
    MessageDetailView,
    # Preference
    PreferenceListCreateView,
    UserPreferenceListCreateView,
    UserPreferenceDestroyView,
)

__all__ = [
    "ProfileView",
    "TaskListCreateView",
    "TaskDetailView",
    "UserModeSettingsView",
    "MatchListCreateView",
    "MatchDetailView",
    "MatchWithUserView",
    "QuestListCreateView",
    "QuestDetailView",
    "ChatListCreateView",
    "ChatDetailView",
    "MessageListCreateView",
    "MessageDetailView",
    "PreferenceListCreateView",
    "UserPreferenceListCreateView",
    "UserPreferenceDestroyView",
]
