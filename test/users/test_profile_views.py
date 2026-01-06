"""
Tests for Profile Views and Serializers
Tests for user profile retrieval and updates
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from users.models import UserProfile, ExpiringToken, Match

User = get_user_model()


class ProfileViewTests(APITestCase):
    """Test profile view"""

    def setUp(self):
        self.profile_url = '/api/profile/'
        self.user = User.objects.create_user(
            email='profile@example.com',
            password='pass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            gender='M',
            nickname='testuser',
            home_latitude=21.0285,
            home_longitude=105.8542
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user)
        self.token = plaintext

    def test_get_profile_requires_authentication(self):
        """Test getting profile requires authentication"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_own_profile(self):
        """Test getting own profile"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Test User')
        self.assertEqual(response.data['gender'], 'M')

    def test_get_profile_includes_user_info(self):
        """Test profile includes user information"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.profile_url)
        self.assertIn('email', response.data)
        self.assertIn('username', response.data)
        self.assertIn('user_id', response.data)

    def test_get_profile_includes_location(self):
        """Test profile includes home location"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.data['home_latitude'], 21.0285)
        self.assertEqual(response.data['home_longitude'], 105.8542)

    def test_update_profile(self):
        """Test updating profile"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'full_name': 'Updated Name',
            'teaser_description': 'New description'
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Updated Name')

    def test_update_profile_partial(self):
        """Test partial profile update"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'nickname': 'newname'}
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Original fields should remain
        self.assertEqual(response.data['full_name'], 'Test User')
        self.assertEqual(response.data['nickname'], 'newname')

    def test_update_location(self):
        """Test updating home location"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'home_latitude': 10.7769,
            'home_longitude': 106.6966
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['home_latitude'], 10.7769)

    def test_update_profile_read_only_fields(self):
        """Test read-only fields cannot be updated"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'is_verified': True,
            'total_xp': 1000,
            'user_id': 999
        }
        response = self.client.put(self.profile_url, data, format='json')
        # Should not update read-only fields
        self.assertFalse(response.data['is_verified'])
        self.assertEqual(response.data['total_xp'], 0)

    def test_update_profile_invalid_data(self):
        """Test updating profile with invalid data"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'home_latitude': 'invalid',
            'home_longitude': 999  # Out of range
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserPublicProfileTests(APITestCase):
    """Test viewing other users' public profiles"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='pass123'
        )
        self.user3 = User.objects.create_user(
            email='user3@example.com',
            password='pass123'
        )
        
        UserProfile.objects.create(
            user=self.user1,
            full_name='User 1',
            nickname='user1nick'
        )
        UserProfile.objects.create(
            user=self.user2,
            full_name='User 2',
            nickname='user2nick'
        )
        UserProfile.objects.create(
            user=self.user3,
            full_name='User 3',
            nickname='user3nick'
        )
        
        # Create a match between user1 and user2
        Match.objects.create(user1=self.user1, user2=self.user2)
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token = plaintext

    def test_view_matched_user_profile(self):
        """Test viewing profile of matched user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/profile/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'User 2')

    def test_cannot_view_unmatched_user_profile(self):
        """Test cannot view profile of unmatched user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/profile/{self.user3.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_profile_requires_authentication(self):
        """Test viewing other profile requires authentication"""
        response = self.client.get(f'/api/profile/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_view_nonexistent_user_profile(self):
        """Test viewing nonexistent user profile"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/profile/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_match_in_either_direction(self):
        """Test profile visible regardless of match direction"""
        # Create match with user2 as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/profile/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProfileSerializerTests(APITestCase):
    """Test UserProfileSerializer"""

    def test_serializer_includes_all_fields(self):
        """Test serializer includes all required fields"""
        user = User.objects.create_user(
            email='serializer@example.com',
            password='pass123'
        )
        profile = UserProfile.objects.create(
            user=user,
            full_name='Full Name',
            gender='F',
            date_of_birth='1995-01-01',
            nickname='nick',
            teaser_description='desc',
            profile_photo_url='https://example.com/photo.jpg',
            verification_video_url='https://example.com/video.mp4',
            is_verified=False,
            total_xp=0,
            is_matched=False,
            home_latitude=21.0285,
            home_longitude=105.8542
        )
        
        plaintext, _ = ExpiringToken.generate_token_for_user(user)
        client = APITestCase()
        client.client.credentials(HTTP_AUTHORIZATION=f'Bearer {plaintext}')
        
        from users.serializers.profile import UserProfileSerializer
        serializer = UserProfileSerializer(profile)
        
        self.assertIn('user_id', serializer.data)
        self.assertIn('email', serializer.data)
        self.assertIn('username', serializer.data)
        self.assertIn('full_name', serializer.data)

    def test_serializer_read_only_fields(self):
        """Test serializer read-only fields"""
        user = User.objects.create_user(
            email='readonly@example.com',
            password='pass123'
        )
        profile = UserProfile.objects.create(user=user)
        
        from users.serializers.profile import UserProfileSerializer
        serializer = UserProfileSerializer(profile)
        
        # These should be read-only
        self.assertIn('user_id', serializer.data)
        self.assertIn('email', serializer.data)
        self.assertIn('username', serializer.data)
