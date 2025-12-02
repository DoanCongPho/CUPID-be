from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class UserRegistrationTests(APITestCase):
    """Test user registration with email/phone_number"""
    
    def setUp(self):
        self.register_url = '/api/auth/register/'
        
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
        
    def test_register_with_all_fields(self):
        """✅ Register with all User and UserProfile fields"""
        data = {
            'email': 'user2@example.com',
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
            'home_longitude': 105.8542
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        user_resp = response.data['user']
        self.assertEqual(user_resp['email'], 'user2@example.com')
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
        # Create first user
        data1 = {
            'email': 'duplicate@example.com',
            'password': 'password123'
        }
        self.client.post(self.register_url, data1, format='json')
        
        # Try to register with same email
        data2 = {
            'email': 'duplicate@example.com',
            'password': 'password456'
        }
        response = self.client.post(self.register_url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_register_duplicate_phone(self):
        """❌ Register with duplicate phone_number should fail"""
        # Create first user
        data1 = {
            'phone_number': '+84999999999',
            'password': 'password123'
        }
        self.client.post(self.register_url, data1, format='json')
        
        # Try to register with same phone
        data2 = {
            'phone_number': '+84999999999',
            'password': 'password456'
        }
        response = self.client.post(self.register_url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_register_invalid_date_format(self):
        """❌ Register with invalid date format should fail"""
        data = {
            'email': 'user3@example.com',
            'password': 'password123',
            'date_of_birth': 'invalid-date'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_register_underage(self):
        """❌ Register with age < 13 should fail"""
        from datetime import datetime, timedelta
        today = datetime.now().date()
        underage_date = (today - timedelta(days=365*12)).isoformat()  # 12 years old
        
        data = {
            'email': 'underage@example.com',
            'password': 'password123',
            'date_of_birth': underage_date
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTests(APITestCase):
    """Test user login with email/phone_number"""
    
    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        
        # Create a test user with email
        self.register_data_email = {
            'email': 'test@example.com',
            'password': 'password123',
            'full_name': 'Test User',
            'nickname': 'testuser'
        }
        self.client.post(self.register_url, self.register_data_email, format='json')
        
        # Create a test user with phone
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