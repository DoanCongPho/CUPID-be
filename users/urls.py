from django.urls import path
from .views import ProfileView, TaskListCreateView, TaskDetailView
from .views_auth import RegisterView, LoginView, LogoutView, TokenListView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/tokens/", TokenListView.as_view(), name="auth-tokens"),
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
]
