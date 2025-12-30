from django.urls import path
from .views import (
    # Authentication
    RegisterView,
    LoginView,
    LogoutView,
    TokenListView,
    # Profile
    ProfileView,
    UserPublicProfileView,
    # Tasks & Settings
    TaskListCreateView,
    TaskDetailView,
    UserModeSettingsView,
    # Matches & Quests
    MatchListCreateView,
    MatchDetailView,
    QuestListCreateView,
    QuestDetailView,
    MatchWithUserView,
    QuestPostHintView,
    MatchRateView,
    SingleUserMatchView,
    # Chats & Messages
    ChatListCreateView,
    ChatDetailView,
    MessageListCreateView,
    MessageDetailView,
    # Preferences
    PreferenceListCreateView,
    UserPreferenceListCreateView,
    UserPreferenceDestroyView,
)

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profiles/<int:user_id>/", UserPublicProfileView.as_view(), name="user-public-profile"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/tokens/", TokenListView.as_view(), name="auth-tokens"),
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path("settings/", UserModeSettingsView.as_view(), name="user-settings"),
    path('matches/', MatchListCreateView.as_view(), name='match-list-create'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='match-detail'),
    path('matches/<int:pk>/rate/', MatchRateView.as_view(), name='match-rate'),
    path('quests/', QuestListCreateView.as_view(), name='quest-list-create'),
    path('quests/<int:pk>/', QuestDetailView.as_view(), name='quest-detail'),
    path('quests/<int:pk>/post-hint/', QuestPostHintView.as_view(), name='quest-post-hint'),
    path('chats/', ChatListCreateView.as_view(), name='chat-list-create'),
    path('chats/<int:pk>/', ChatDetailView.as_view(), name='chat-detail'),
    path('chats/<int:chat_pk>/messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    path('matches/with/<int:user_id>/', MatchWithUserView.as_view(), name='match-with-user'),
    path('match/singles/', SingleUserMatchView.as_view(), name='match-singles'),
    # Preferences API
    path('preferences/', PreferenceListCreateView.as_view(), name='preference-list-create'),
    path('user-preferences/', UserPreferenceListCreateView.as_view(), name='user-preference-list-create'),
    path('user-preferences/<int:pref_id>/', UserPreferenceDestroyView.as_view(), name='user-preference-destroy'),
]
