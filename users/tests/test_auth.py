"""
Authentication API Tests
Tests for user registration, login, logout, and token management
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import UserProfile, ExpiringToken, Preference, UserPreference
from datetime import datetime, timedelta

User = get_user_model()


class UserRegistrationTests(APITestCase):
    """Test user registration with email/phone_number and preferences"""

    def setUp(self):
        self.register_url = '/api/auth/register/'
        # Create some preferences for testing
        self.pref1 = Preference.objects.create(name="Books")
        self.pref2 = Preference.objects.create(name="Gym")
        self.pref3 = Preference.objects.create(name="Coffee")

    def test_register_with_email_only(self):
        """✅ Register with email + password"""
        data = {
            'email': 'user1@example.com',
            'password': 'password123',
            'full_name': 'John Doe',
            'nickname': 'john'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'user1@example.com')
        self.assertEqual(response.data['user']['full_name'], 'John Doe')

    def test_register_with_phone_only(self):
        """✅ Register with phone_number + password"""
        data = {
            'phone_number': '+84901234567',
            'password': 'password123',
            'full_name': 'Jane Doe',
            'nickname': 'jane'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['phone_number'], '+84901234567')
        self.assertEqual(response.data['user']['full_name'], 'Jane Doe')

    def test_register_with_preferences(self):
        """✅ Register with preferences"""
        data = {
            'email': 'user2@example.com',
            'password': 'password123',
            'full_name': 'Test User',
            'preferences': [self.pref1.id, self.pref2.id]
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check preferences were attached
        user = User.objects.get(email='user2@example.com')
        user_prefs = UserPreference.objects.filter(user=user)
        self.assertEqual(user_prefs.count(), 2)

    def test_register_with_all_fields(self):
        """✅ Register with all User and UserProfile fields"""
        data = {
            'email': 'user3@example.com',
            'phone_number': '+84912345678',
            'password': 'password123',
            'provider': 'email',
            'full_name': 'Test User',
            'nickname': 'testuser',
            'date_of_birth': '1995-05-15',
            'teaser_description': 'Software engineer',
            'profile_photo_url': 'https://example.com/photo.jpg',
            'verification_video_url': 'https://example.com/video.mp4',
            'home_latitude': 21.0285,
            'home_longitude': 105.8542,
            'preferences': [self.pref1.id, self.pref3.id]
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        user_resp = response.data['user']
        self.assertEqual(user_resp['email'], 'user3@example.com')
        self.assertEqual(user_resp['phone_number'], '+84912345678')
        self.assertEqual(user_resp['full_name'], 'Test User')
        self.assertEqual(user_resp['home_latitude'], 21.0285)

    def test_register_without_email_and_phone(self):
        """❌ Register without email and phone_number should fail"""
        data = {
            'password': 'password123',
            'full_name': 'Invalid User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """❌ Register with duplicate email should fail"""
        data1 = {
            'email': 'duplicate@example.com',
            'password': 'password123'
        }
        self.client.post(self.register_url, data1, format='json')

        data2 = {
            'email': 'duplicate@example.com',
            'password': 'password456'
        }
        response = self.client.post(self.register_url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_phone(self):
        """❌ Register with duplicate phone_number should fail"""
        data1 = {
            'phone_number': '+84999999999',
            'password': 'password123'
        }
        self.client.post(self.register_url, data1, format='json')

        data2 = {
            'phone_number': '+84999999999',
            'password': 'password456'
        }
        response = self.client.post(self.register_url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_date_format(self):
        """❌ Register with invalid date format should fail"""
        data = {
            'email': 'user4@example.com',
            'password': 'password123',
            'date_of_birth': 'invalid-date'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_underage(self):
        """❌ Register with age < 13 should fail"""
        today = datetime.now().date()
        underage_date = (today - timedelta(days=365*12)).isoformat()  # 12 years old

        data = {
            'email': 'underage@example.com',
            'password': 'password123',
            'date_of_birth': underage_date
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_future_date_of_birth(self):
        """❌ Register with future date of birth should fail"""
        today = datetime.now().date()
        future_date = (today + timedelta(days=365)).isoformat()

        data = {
            'email': 'future@example.com',
            'password': 'password123',
            'date_of_birth': future_date
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTests(APITestCase):
    """Test user login with email/phone_number"""

    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'

        # Create test user with email
        self.register_data_email = {
            'email': 'test@example.com',
            'password': 'password123',
            'full_name': 'Test User',
            'nickname': 'testuser'
        }
        self.client.post(self.register_url, self.register_data_email, format='json')

        # Create test user with phone
        self.register_data_phone = {
            'phone_number': '+84901234567',
            'password': 'password456',
            'full_name': 'Phone User',
            'nickname': 'phoneuser'
        }
        self.client.post(self.register_url, self.register_data_phone, format='json')

    def test_login_with_email(self):
        """✅ Login with email + password"""
        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('expires_at', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')

    def test_login_with_phone(self):
        """✅ Login with phone_number + password"""
        data = {
            'phone_number': '+84901234567',
            'password': 'password456'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['phone_number'], '+84901234567')

    def test_login_wrong_password(self):
        """❌ Login with wrong password should fail"""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """❌ Login with non-existent email should fail"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_without_email_and_phone(self):
        """❌ Login without email and phone_number should fail"""
        data = {
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_full_user_info(self):
        """✅ Login returns all user and profile information"""
        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_resp = response.data['user']

        # Check User fields
        self.assertIn('id', user_resp)
        self.assertIn('email', user_resp)
        self.assertIn('phone_number', user_resp)
        self.assertIn('provider', user_resp)

        # Check UserProfile fields
        self.assertIn('full_name', user_resp)
        self.assertIn('nickname', user_resp)
        self.assertIn('date_of_birth', user_resp)
        self.assertIn('profile_photo_url', user_resp)
        self.assertIn('is_verified', user_resp)
        self.assertIn('total_xp', user_resp)

    def test_login_case_insensitive_email(self):
        """✅ Login with email is case-insensitive"""
        data = {
            'email': 'TEST@EXAMPLE.COM',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LogoutTests(APITestCase):
    """Test user logout and token revocation"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.logout_url = '/api/auth/logout/'

    def test_logout_revokes_token(self):
        """✅ Logout revokes the token"""
        # Generate token
        token_plain, token_obj = ExpiringToken.generate_token_for_user(self.user, days_valid=365, name="test")

        # Authenticate with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_plain}')

        # Logout
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)

        # Check token is revoked
        token_obj.refresh_from_db()
        self.assertTrue(token_obj.revoked)

    def test_logout_without_authentication(self):
        """❌ Logout without authentication should fail"""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TokenManagementTests(APITestCase):
    """Test token listing and management"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.tokens_url = '/api/auth/tokens/'

    def test_list_user_tokens(self):
        """✅ List all tokens for authenticated user"""
        # Generate multiple tokens
        ExpiringToken.generate_token_for_user(self.user, days_valid=365, name="token1")
        ExpiringToken.generate_token_for_user(self.user, days_valid=365, name="token2")

        # Authenticate
        token_plain, _ = ExpiringToken.generate_token_for_user(self.user, days_valid=365, name="token3")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_plain}')

        # List tokens
        response = self.client.get(self.tokens_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # Check token fields
        token_data = response.data[0]
        self.assertIn('id', token_data)
        self.assertIn('name', token_data)
        self.assertIn('created_at', token_data)
        self.assertIn('expires_at', token_data)
        self.assertIn('revoked', token_data)

    def test_list_tokens_without_authentication(self):
        """❌ List tokens without authentication should fail"""
        response = self.client.get(self.tokens_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
