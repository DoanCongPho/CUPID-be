"""
Tests for the fallback to Auth0's /userinfo endpoint when a JWT carries no
email claim.

This module used to be written in pytest style (bare functions plus the
monkeypatch fixture), which `manage.py test` could not collect. It now uses
unittest/APITestCase with unittest.mock.patch instead.
"""
from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient

import users.authentication as auth_mod
from users.authentication import fetch_userinfo, Auth0JSONWebTokenAuthentication

User = get_user_model()


class FakeResponse:
    """Stand-in response for requests.get"""

    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError()


# AUTH0_DOMAIN is unset locally, so fetch_userinfo would break on
# settings.AUTH0_DOMAIN.rstrip(...); override it so the test does not depend on .env
@override_settings(AUTH0_DOMAIN="test.auth0.com")
class FetchUserinfoTests(APITestCase):
    """Unit tests for the fetch_userinfo helper"""

    def test_fetch_userinfo_returns_json(self):
        fake_userinfo = {
            "sub": "auth0|123456",
            "email": "fetched@example.com",
            "email_verified": True,
            "nickname": "fetched",
        }

        with patch("requests.get", return_value=FakeResponse(fake_userinfo)):
            userinfo = fetch_userinfo("fake-access-token")

        self.assertIsInstance(userinfo, dict)
        self.assertEqual(userinfo["email"], "fetched@example.com")
        self.assertEqual(userinfo["sub"], "auth0|123456")


class UserinfoFallbackTests(APITestCase):
    """A token without an email claim makes authenticate() call fetch_userinfo"""

    def test_profile_view_with_missing_email_uses_userinfo(self):
        def fake_fetch_userinfo(access_token):
            return {
                "sub": "auth0|fallback123",
                "email": "fallback@example.com",
                "email_verified": True,
                "nickname": "fallback",
            }

        def fake_validate_token(self, token):
            # the payload deliberately omits "email" to trigger the fallback branch
            return {"sub": "auth0|fallback123", "name": "fallback"}

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer faketoken")

        with patch.object(auth_mod, "fetch_userinfo", fake_fetch_userinfo), \
             patch.object(Auth0JSONWebTokenAuthentication, "_validate_token", fake_validate_token):
            response = client.get("/api/profile/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("email"), "fallback@example.com")
        # authenticate() derives the username from the local part of the email
        self.assertEqual(data.get("username"), "fallback")
