"""
Tests for Auth0JSONWebTokenAuthentication and ProfileView.

This module used to be written in pytest style (bare functions plus the
monkeypatch fixture), which `manage.py test` could not collect. It now uses
unittest/APITestCase with unittest.mock.patch instead.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APITestCase, APIClient

from users.authentication import Auth0JSONWebTokenAuthentication
from users.views import ProfileView

User = get_user_model()


class Auth0AuthenticationTests(APITestCase):
    """ProfileView combined with the Auth0 authentication class"""

    def test_profile_view_authenticated(self):
        """
        When authentication yields a valid user, ProfileView must return 200
        along with that user's email.
        """
        user = User.objects.create_user(
            username="t_test", email="t_test@example.com", password="password"
        )

        def fake_authenticate(self, request):
            return (user, None)

        with patch.object(Auth0JSONWebTokenAuthentication, "authenticate", fake_authenticate):
            request = RequestFactory().get(
                "/api/profile/", HTTP_AUTHORIZATION="Bearer faketoken"
            )
            response = ProfileView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data.get("email"), "t_test@example.com")

    def test_profile_view_invalid_token(self):
        """A bad token raises AuthenticationFailed and yields 401 (or 403)"""

        def fake_auth_fail(self, request):
            raise AuthenticationFailed("invalid token")

        with patch.object(Auth0JSONWebTokenAuthentication, "authenticate", fake_auth_fail):
            request = RequestFactory().get(
                "/api/profile/", HTTP_AUTHORIZATION="Bearer invalid"
            )
            response = ProfileView.as_view()(request)

        self.assertIn(response.status_code, (401, 403))

    def test_profile_view_force_authenticate(self):
        """force_authenticate makes the endpoint return the signed-in user's data"""
        user = User.objects.create_user(
            username="force_user", email="force@example.com", password="password"
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/profile/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("email"), "force@example.com")
        self.assertEqual(data.get("username"), "force_user")
