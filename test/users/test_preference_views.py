"""
Tests for Preference Views and Serializers
Tests for preference management and user preferences
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from users.models import Preference, UserPreference, ExpiringToken

User = get_user_model()


class PreferenceListTests(APITestCase):
    """Test preference list endpoint"""

    def setUp(self):
        self.pref_url = '/api/preferences/'
        self.pref1 = Preference.objects.create(name='Books')
        self.pref2 = Preference.objects.create(name='Gym')
        self.pref3 = Preference.objects.create(name='Coffee')

    def test_list_preferences_no_auth(self):
        """Test listing preferences doesn't require authentication"""
        response = self.client.get(self.pref_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_preferences_ordered_by_name(self):
        """Test preferences are ordered alphabetically"""
        response = self.client.get(self.pref_url)
        names = [p['name'] for p in response.data]
        self.assertEqual(names, ['Books', 'Coffee', 'Gym'])

    def test_preferences_include_id(self):
        """Test preferences include id field"""
        response = self.client.get(self.pref_url)
        self.assertGreater(len(response.data), 0)
        self.assertIn('id', response.data[0])
        self.assertIn('name', response.data[0])

    def test_create_preference_no_auth(self):
        """Test creating preference doesn't require authentication"""
        data = {'name': 'Swimming'}
        response = self.client.post(self.pref_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_duplicate_preference(self):
        """Test creating duplicate preference fails"""
        data = {'name': 'Books'}
        response = self.client.post(self.pref_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_preference_response(self):
        """Test create preference response"""
        data = {'name': 'Hiking'}
        response = self.client.post(self.pref_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Hiking')
        self.assertIn('id', response.data)


class UserPreferenceListTests(APITestCase):
    """Test user preference endpoints"""

    def setUp(self):
        self.user_pref_url = '/api/user-preferences/'
        self.user = User.objects.create_user(
            email='prefuser@example.com',
            password='pass123'
        )
        self.pref1 = Preference.objects.create(name='Books')
        self.pref2 = Preference.objects.create(name='Gym')
        self.pref3 = Preference.objects.create(name='Coffee')
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user)
        self.token = plaintext

    def test_list_user_preferences_requires_auth(self):
        """Test listing user preferences requires authentication"""
        response = self.client.get(self.user_pref_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_preferences(self):
        """Test listing user's preferences"""
        UserPreference.objects.create(user=self.user, preference=self.pref1)
        UserPreference.objects.create(user=self.user, preference=self.pref2)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.user_pref_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_user_preferences_empty_list(self):
        """Test empty preferences list"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.user_pref_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_add_user_preference(self):
        """Test adding preference to user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'preference_id': self.pref1.id}
        response = self.client.post(self.user_pref_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_duplicate_preference(self):
        """Test adding duplicate preference creates only one"""
        UserPreference.objects.create(user=self.user, preference=self.pref1)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'preference_id': self.pref1.id}
        response = self.client.post(self.user_pref_url, data, format='json')
        
        # Should still succeed (get_or_create behavior)
        prefs = UserPreference.objects.filter(user=self.user, preference=self.pref1)
        self.assertEqual(prefs.count(), 1)

    def test_user_preferences_ordered_by_created(self):
        """Test user preferences ordered by creation date"""
        up1 = UserPreference.objects.create(user=self.user, preference=self.pref1)
        up2 = UserPreference.objects.create(user=self.user, preference=self.pref2)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.user_pref_url)
        
        ids = [p['preference']['id'] for p in response.data]
        self.assertEqual(ids[0], self.pref1.id)
        self.assertEqual(ids[1], self.pref2.id)

    def test_preference_details_in_list(self):
        """Test preference details included in list"""
        UserPreference.objects.create(user=self.user, preference=self.pref1)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.user_pref_url)
        
        pref_data = response.data[0]['preference']
        self.assertEqual(pref_data['name'], 'Books')
        self.assertEqual(pref_data['id'], self.pref1.id)


class UserPreferenceDestroyTests(APITestCase):
    """Test removing user preferences"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='deluser@example.com',
            password='pass123'
        )
        self.pref1 = Preference.objects.create(name='Books')
        self.pref2 = Preference.objects.create(name='Gym')
        UserPreference.objects.create(user=self.user, preference=self.pref1)
        UserPreference.objects.create(user=self.user, preference=self.pref2)
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user)
        self.token = plaintext

    def test_remove_user_preference(self):
        """Test removing a user preference"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete(f'/api/user-preferences/{self.pref1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check it was deleted
        prefs = UserPreference.objects.filter(user=self.user, preference=self.pref1)
        self.assertEqual(prefs.count(), 0)

    def test_remove_nonexistent_preference(self):
        """Test removing nonexistent preference"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete(f'/api/user-preferences/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_remove_other_user_preference(self):
        """Test cannot remove other user's preference"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='pass123'
        )
        other_pref = Preference.objects.create(name='Swimming')
        UserPreference.objects.create(user=other_user, preference=other_pref)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete(f'/api/user-preferences/{other_pref.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_requires_authentication(self):
        """Test removing preference requires authentication"""
        response = self.client.delete(f'/api/user-preferences/{self.pref1.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PreferenceSerializerTests(APITestCase):
    """Test preference serializers"""

    def test_preference_serializer_fields(self):
        """Test PreferenceSerializer includes correct fields"""
        pref = Preference.objects.create(name='Travel')
        
        from users.serializers.preference import PreferenceSerializer
        serializer = PreferenceSerializer(pref)
        
        self.assertIn('id', serializer.data)
        self.assertIn('name', serializer.data)
        self.assertEqual(serializer.data['name'], 'Travel')

    def test_user_preference_serializer(self):
        """Test UserPreferenceSerializer"""
        user = User.objects.create_user(
            email='serialize@example.com',
            password='pass123'
        )
        pref = Preference.objects.create(name='Art')
        up = UserPreference.objects.create(user=user, preference=pref)
        
        from users.serializers.preference import UserPreferenceSerializer
        serializer = UserPreferenceSerializer(up)
        
        self.assertIn('preference', serializer.data)
        self.assertIn('created_at', serializer.data)
        self.assertEqual(serializer.data['preference']['name'], 'Art')
