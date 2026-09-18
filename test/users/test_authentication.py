"""
Tests cho Auth0JSONWebTokenAuthentication và ProfileView.

Trước đây file này viết theo kiểu pytest (hàm rời + fixture monkeypatch), nên
`manage.py test` không chạy được. Đã chuyển sang unittest/APITestCase và dùng
unittest.mock.patch thay cho monkeypatch.
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
    """ProfileView kết hợp với Auth0 authentication class"""

    def test_profile_view_authenticated(self):
        """
        Giả lập authentication trả về user hợp lệ -> ProfileView phải trả 200
        kèm email của user đó.
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
        """Token hỏng -> AuthenticationFailed -> 401 (hoặc 403)"""

        def fake_auth_fail(self, request):
            raise AuthenticationFailed("invalid token")

        with patch.object(Auth0JSONWebTokenAuthentication, "authenticate", fake_auth_fail):
            request = RequestFactory().get(
                "/api/profile/", HTTP_AUTHORIZATION="Bearer invalid"
            )
            response = ProfileView.as_view()(request)

        self.assertIn(response.status_code, (401, 403))

    def test_profile_view_force_authenticate(self):
        """force_authenticate -> endpoint trả đúng dữ liệu của user đang đăng nhập"""
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
