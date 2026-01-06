"""
Tests for Authentication Views and Serializers
Tests for register, login, logout, and token management
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from users.models import UserProfile, ExpiringToken, Preference, UserPreference

User = get_user_model()


class UserRegistrationTests(APITestCase):
    """Test user registration endpoint"""

    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.pref1 = Preference.objects.create(name="Books")
        self.pref2 = Preference.objects.create(name="Gym")
        self.pref3 = Preference.objects.create(name="Coffee")

    def test_register_with_email_only(self):
        """Test registration with email and password"""
        data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'full_name': 'John Doe'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertEqual(response.data['user']['full_name'], 'John Doe')

    def test_register_with_phone_number(self):
        """Test registration with phone number"""
        data = {
            'phone_number': '+84901234567',
            'password': 'securepass123',
            'full_name': 'Jane Doe'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['phone_number'], '+84901234567')

    def test_register_with_both_email_and_phone(self):
        """Test registration with both email and phone number"""
        data = {
            'email': 'both@example.com',
            'phone_number': '+84987654321',
            'password': 'securepass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_without_email_and_phone(self):
        """Test registration fails without email or phone"""
        data = {'password': 'securepass123'}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails"""
        data = {
            'email': 'duplicate@example.com',
            'password': 'pass123'
        }
        self.client.post(self.register_url, data, format='json')
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_phone(self):
        """Test registration with duplicate phone fails"""
        data = {
            'phone_number': '+84999999999',
            'password': 'pass123'
        }
        self.client.post(self.register_url, data, format='json')
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_all_profile_fields(self):
        """Test registration with all profile fields"""
        data = {
            'email': 'complete@example.com',
            'phone_number': '+84912345678',
            'password': 'securepass123',
            'full_name': 'Complete User',
            'nickname': 'completeuser',
            'gender': 'M',
            'date_of_birth': '1995-05-15',
            'teaser_description': 'Software Engineer',
            'profile_photo_url': 'https://example.com/photo.jpg',
            'verification_video_url': 'https://example.com/video.mp4',
            'home_latitude': 21.0285,
            'home_longitude': 105.8542
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_data = response.data['user']
        self.assertEqual(user_data['full_name'], 'Complete User')
        self.assertEqual(user_data['home_latitude'], 21.0285)

    def test_register_with_preferences(self):
        """Test registration with preferences"""
        data = {
            'email': 'prefs@example.com',
            'password': 'securepass123',
            'preferences': [self.pref1.id, self.pref2.id]
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email='prefs@example.com')
        user_prefs = UserPreference.objects.filter(user=user)
        self.assertEqual(user_prefs.count(), 2)

    def test_register_invalid_date_format(self):
        """Test registration with invalid date format"""
        data = {
            'email': 'baddate@example.com',
            'password': 'securepass123',
            'date_of_birth': 'invalid-date'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_underage(self):
        """Test registration with age < 13 fails"""
        today = datetime.now().date()
        underage_date = (today - timedelta(days=365*12)).isoformat()
        
        data = {
            'email': 'underage@example.com',
            'password': 'securepass123',
            'date_of_birth': underage_date
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_future_date(self):
        """Test registration with future date fails"""
        tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
        
        data = {
            'email': 'future@example.com',
            'password': 'securepass123',
            'date_of_birth': tomorrow
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        """Test registration with short password fails"""
        data = {
            'email': 'shortpass@example.com',
            'password': 'short'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_url(self):
        """Test registration with invalid URL fails"""
        data = {
            'email': 'badurl@example.com',
            'password': 'securepass123',
            'profile_photo_url': 'not-a-url'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_creates_profile(self):
        """Test that registration creates UserProfile"""
        data = {
            'email': 'profile@example.com',
            'password': 'securepass123'
        }
        self.client.post(self.register_url, data, format='json')
        
        user = User.objects.get(email='profile@example.com')
        self.assertTrue(hasattr(user, 'profile'))

    def test_registration_creates_token(self):
        """Test that registration creates ExpiringToken"""
        data = {
            'email': 'token@example.com',
            'password': 'securepass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        user = User.objects.get(email='token@example.com')
        tokens = ExpiringToken.objects.filter(user=user)
        self.assertGreater(tokens.count(), 0)


class UserLoginTests(APITestCase):
    """Test user login endpoint"""

    def setUp(self):
        self.login_url = '/api/auth/login/'
        self.user = User.objects.create_user(
            email='loginuser@example.com',
            phone_number='+84901111111',
            password='loginpass123'
        )
        UserProfile.objects.create(user=self.user)

    def test_login_with_email(self):
        """Test login with email"""
        data = {
            'email': 'loginuser@example.com',
            'password': 'loginpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'loginuser@example.com')

    def test_login_with_phone(self):
        """Test login with phone number"""
        data = {
            'phone_number': '+84901111111',
            'password': 'loginpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_wrong_password(self):
        """Test login with wrong password fails"""
        data = {
            'email': 'loginuser@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user fails"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'pass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        """Test login with inactive user fails"""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'email': 'loginuser@example.com',
            'password': 'loginpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_without_email_and_phone(self):
        """Test login without email or phone fails"""
        data = {'password': 'pass123'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_user_info(self):
        """Test login response includes user information"""
        data = {
            'email': 'loginuser@example.com',
            'password': 'loginpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        user_data = response.data['user']
        
        self.assertIn('id', user_data)
        self.assertIn('email', user_data)
        self.assertIn('phone_number', user_data)

    def test_login_creates_new_token(self):
        """Test each login creates a new token"""
        data = {
            'email': 'loginuser@example.com',
            'password': 'loginpass123'
        }
        
        response1 = self.client.post(self.login_url, data, format='json')
        response2 = self.client.post(self.login_url, data, format='json')
        
        token1 = response1.data['token']
        token2 = response2.data['token']
        self.assertNotEqual(token1, token2)


class UserLogoutTests(APITestCase):
    """Test user logout endpoint"""

    def setUp(self):
        self.logout_url = '/api/auth/logout/'
        self.user = User.objects.create_user(
            email='logoutuser@example.com',
            password='logoutpass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user)
        self.token = plaintext

    def test_logout_requires_authentication(self):
        """Test logout requires authenticated user"""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_revokes_token(self):
        """Test logout revokes the token"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Token should be revoked
        token_obj = ExpiringToken.verify_token(self.token)
        self.assertIsNone(token_obj)

    def test_logout_response(self):
        """Test logout response message"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post(self.logout_url)
        self.assertIn('detail', response.data)


class TokenListTests(APITestCase):
    """Test token list endpoint"""

    def setUp(self):
        self.list_url = '/api/auth/tokens/'
        self.user = User.objects.create_user(
            email='tokenuser@example.com',
            password='tokenpass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(
            self.user,
            name='token1'
        )
        self.token = plaintext

    def test_list_tokens_requires_authentication(self):
        """Test listing tokens requires authentication"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_tokens(self):
        """Test listing user tokens"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_list_tokens_returns_only_user_tokens(self):
        """Test listing returns only current user's tokens"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='pass123'
        )
        ExpiringToken.generate_token_for_user(other_user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.list_url)
        
        self.assertEqual(len(response.data), 1)

    def test_token_list_contains_metadata(self):
        """Test token list includes token metadata"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.list_url)
        
        token_data = response.data[0]
        self.assertIn('id', token_data)
        self.assertIn('name', token_data)
        self.assertIn('created_at', token_data)
        self.assertIn('expires_at', token_data)
        self.assertIn('revoked', token_data)
