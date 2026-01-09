"""
Backward compatibility shim for authentication views.
Imports from the new views package.
"""
from .views.auth import (
    RegisterView,
    LoginView,
    LogoutView,
    TokenListView,
)

__all__ = [
    "RegisterView",
    "LoginView",
    "LogoutView",
    "TokenListView",
]
