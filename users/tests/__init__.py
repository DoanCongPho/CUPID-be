"""
Users App Tests Package

Organized test structure:
- test_auth.py: Authentication tests (registration, login, logout, tokens)
- test_services.py: Service tests (profile, tasks, matches, quests, chats, preferences)

All tests can be run with: python manage.py test users
"""

# Import all test cases from submodules
from .test_auth import (
    UserRegistrationTests,
    UserLoginTests,
    LogoutTests,
    TokenManagementTests,
)

from .test_services import (
    UserProfileTests,
    TaskAPITests,
    UserModeSettingsAPITests,
    MatchAPITests,
    QuestAPITests,
    ChatAndMessageAPITests,
    PreferenceAPITests,
)


__all__ = [
    # Authentication tests
    "UserRegistrationTests",
    "UserLoginTests",
    "LogoutTests",
    "TokenManagementTests",
    # Service tests
    "UserProfileTests",
    "TaskAPITests",
    "UserModeSettingsAPITests",
    "MatchAPITests",
    "QuestAPITests",
    "ChatAndMessageAPITests",
    "PreferenceAPITests",
]
