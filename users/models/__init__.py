"""
Users App Models Package

Organized model structure:
- user.py: User authentication model
- token.py: ExpiringToken for token-based auth
- profile.py: UserProfile and UserModeSettings
- task.py: Task model
- match.py: Match and Quests models
- chat.py: Chat and Message models
- preference.py: Preference and UserPreference models

IMPORTANT: Import order matters to avoid circular dependencies!
1. User model first (other models depend on it)
2. Independent models (Token, Profile, Task, Preference)
3. Models with relationships (Match)
4. Models depending on Match (Chat)
"""

# 1. Import User model first (required by AUTH_USER_MODEL)
from .user import User

# 2. Import independent models (no inter-model dependencies)
from .token import ExpiringToken
from .profile import UserProfile, UserModeSettings
from .task import Task
from .preference import Preference, UserPreference

# 3. Import Match models (depends on User)
from .match import Match, Quests

# 4. Import Chat models last (depends on Match)
from .chat import Chat, Message


# Export all models for backward compatibility
__all__ = [
    # Authentication
    "User",
    "ExpiringToken",
    # Profile
    "UserProfile",
    "UserModeSettings",
    # Task
    "Task",
    # Matching
    "Match",
    "Quests",
    # Chat
    "Chat",
    "Message",
    # Preference
    "Preference",
    "UserPreference",
]
