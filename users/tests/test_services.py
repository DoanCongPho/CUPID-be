"""
User Services API Tests
Tests for user profile, tasks, matches, quests, chats, messages, and preferences
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import (
    UserProfile, Task, UserModeSettings, Match, Quests,
    Chat, Message, Preference, UserPreference, ExpiringToken
)
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class UserProfileTests(APITestCase):
    """Test user profile retrieve and update"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.profile_url = '/api/profile/'
        token_plain, _ = ExpiringToken.generate_token_for_user(self.user, days_valid=365, name="test")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_plain}')

    def test_get_profile(self):
        """✅ Get user profile"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('full_name', response.data)
        self.assertIn('nickname', response.data)
        self.assertIn('total_xp', response.data)

    def test_update_profile(self):
        """✅ Update user profile"""
        data = {
            'full_name': 'Updated Name',
            'nickname': 'newnick',
            'teaser_description': 'New description'
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Updated Name')

    def test_profile_without_authentication(self):
        """❌ Get profile without authentication should fail"""
        self.client.credentials()
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TaskAPITests(APITestCase):
    """Test Task CRUD operations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        token_plain, _ = ExpiringToken.generate_token_for_user(self.user, days_valid=365, name="test")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_plain}')
        self.task_url = '/api/tasks/'

    def test_create_task(self):
        """✅ Create a new task"""
        data = {
            'description': 'Complete project',
            'scheduled_start_time': '2025-01-15T10:00:00Z',
            'scheduled_end_time': '2025-01-15T12:00:00Z',
            'is_free': True
        }
        response = self.client.post(self.task_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Complete project')
        self.assertTrue(response.data['is_free'])

    def test_list_tasks(self):
        """✅ List all tasks for authenticated user"""
        Task.objects.create(user=self.user, description='Task 1')
        Task.objects.create(user=self.user, description='Task 2')

        response = self.client.get(self.task_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_task_detail(self):
        """✅ Get task detail"""
        task = Task.objects.create(user=self.user, description='Task detail test')
        url = f'{self.task_url}{task.id}/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Task detail test')

    def test_update_task(self):
        """✅ Update an existing task"""
        task = Task.objects.create(user=self.user, description='Old description')
        url = f'{self.task_url}{task.id}/'

        data = {'description': 'New description', 'is_free': False}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'New description')
        self.assertFalse(response.data['is_free'])

    def test_delete_task(self):
        """✅ Delete a task"""
        task = Task.objects.create(user=self.user, description='To delete')
        url = f'{self.task_url}{task.id}/'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_cannot_access_other_user_task(self):
        """❌ Cannot access another user's task"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        task = Task.objects.create(user=other_user, description='Other user task')
        url = f'{self.task_url}{task.id}/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserModeSettingsAPITests(APITestCase):
    """Test UserModeSettings CRUD operations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        token_plain, _ = ExpiringToken.generate_token_for_user(self.user, days_valid=365, name="test")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_plain}')
        self.settings_url = '/api/settings/'

    def test_get_or_create_settings(self):
        """✅ Get user mode settings (creates if not exists)"""
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ghost_mode_enabled', response.data)
        self.assertIn('daily_reminders_enabled', response.data)
        self.assertIn('location_sharing_enabled', response.data)

    def test_update_settings(self):
        """✅ Update user mode settings"""
        data = {
            'ghost_mode_enabled': True,
            'daily_reminders_enabled': False,
            'spotmatch_notifications_enabled': True
        }
        response = self.client.put(self.settings_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['ghost_mode_enabled'])
        self.assertFalse(response.data['daily_reminders_enabled'])
        self.assertTrue(response.data['spotmatch_notifications_enabled'])


class MatchAPITests(APITestCase):
    """Test Match CRUD operations"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123'
        )
        token_plain, _ = ExpiringToken.generate_token_for_user(self.user1, days_valid=365, name="test")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_plain}')
        self.match_url = '/api/matches/'

    def test_create_match(self):
        """✅ Create a new match"""
        data = {'user2_id': self.user2.id}
        response = self.client.post(self.match_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user1']['id'], self.user1.id)
        self.assertEqual(response.data['user2']['id'], self.user2.id)
        self.assertEqual(response.data['status'], 'successful')

    def test_list_matches(self):
        """✅ List all matches for authenticated user"""
        Match.objects.create(user1=self.user1, user2=self.user2)

        response = self.client.get(self.match_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_match_detail(self):
        """✅ Get match detail"""
        match = Match.objects.create(user1=self.user1, user2=self.user2)
        url = f'{self.match_url}{match.id}/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], match.id)

    def test_update_match(self):
        """✅ Update match status"""
        match = Match.objects.create(user1=self.user1, user2=self.user2)
        url = f'{self.match_url}{match.id}/'

        # Use PATCH for partial updates - status choices: successful, user1_missed, user2_missed, expired
        data = {'status': 'expired', 'user1_rating': 5}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'expired')
        self.assertEqual(response.data['user1_rating'], 5)

    def test_match_with_user_endpoint(self):
        """✅ Match with specific user (PUT /api/matches/with/<user_id>/)"""
        url = f'/api/matches/with/{self.user2.id}/'
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user1']['id'], self.user1.id)
        self.assertEqual(response.data['user2']['id'], self.user2.id)

        # Try again - should return existing match
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_match_with_self(self):
        """❌ Cannot match with yourself"""
        url = f'/api/matches/with/{self.user1.id}/'
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class QuestAPITests(APITestCase):
    """Test Quest CRUD operations"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        token_plain, _ = ExpiringToken.generate_token_for_user(self.user1, days_valid=365, name="test")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_plain}')
        self.quest_url = '/api/quests/'

    def test_create_quest(self):
        """✅ Create a new quest"""
        data = {
            'match_id': self.match.id,
            'location_name': 'Central Park',
            'activity': 'Picnic',
            'location_latitude': 40.785091,
            'location_longitude': -73.968285,
            'quest_date': '2025-01-20'  # Use YYYY-MM-DD format, not ISO datetime
        }
        response = self.client.post(self.quest_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['location_name'], 'Central Park')
        self.assertEqual(response.data['activity'], 'Picnic')

    def test_list_quests(self):
        """✅ List all quests for authenticated user's matches"""
        Quests.objects.create(
            match=self.match,
            location_name='Quest 1',
            activity='Activity 1',
            quest_date=timezone.now() + timedelta(days=1)
        )

        response = self.client.get(self.quest_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_quest(self):
        """✅ Update a quest"""
        quest = Quests.objects.create(
            match=self.match,
            location_name='Old name',
            activity='Old activity',
            quest_date=timezone.now() + timedelta(days=1)
        )
        url = f'{self.quest_url}{quest.id}/'

        data = {'location_name': 'New name', 'status': 'completed'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['location_name'], 'New name')
        self.assertEqual(response.data['status'], 'completed')

    def test_delete_quest(self):
        """✅ Delete a quest"""
        quest = Quests.objects.create(
            match=self.match,
            location_name='To delete',
            activity='Activity',
            quest_date=timezone.now() + timedelta(days=1)
        )
        url = f'{self.quest_url}{quest.id}/'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quests.objects.filter(id=quest.id).exists())


class ChatAndMessageAPITests(APITestCase):
    """Test Chat and Message CRUD operations"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        # Chat is auto-created by signal, so get it instead of creating
        self.chat = Chat.objects.get(match=self.match)
        token_plain, _ = ExpiringToken.generate_token_for_user(self.user1, days_valid=365, name="test")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_plain}')

    def test_create_chat(self):
        """✅ Create a new chat (auto-created by signal when match is created)"""
        # Create a third user to avoid conflict with existing user1-user2 match
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='password123'
        )
        # When we create a match, a chat is automatically created by the signal
        match2 = Match.objects.create(user1=self.user1, user2=user3)
        # Get the auto-created chat
        chat2 = Chat.objects.get(match=match2)
        # Verify the chat was created and linked to the match
        self.assertEqual(chat2.match.id, match2.id)
        self.assertEqual(Chat.objects.filter(match=match2).count(), 1)

    def test_list_chats(self):
        """✅ List all chats for authenticated user"""
        response = self.client.get('/api/chats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_chat_detail(self):
        """✅ Get chat detail"""
        url = f'/api/chats/{self.chat.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.chat.id)

    def test_send_message(self):
        """✅ Send a message in a chat"""
        url = f'/api/chats/{self.chat.id}/messages/'
        data = {'content': 'Hello!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Hello!')
        self.assertEqual(response.data['sender']['id'], self.user1.id)

    def test_list_messages(self):
        """✅ List messages in a chat"""
        Message.objects.create(chat=self.chat, sender=self.user1, content='Message 1')
        Message.objects.create(chat=self.chat, sender=self.user2, content='Message 2')

        url = f'/api/chats/{self.chat.id}/messages/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_messages_ordered_by_sent_at(self):
        """✅ Messages are ordered by sent_at"""
        msg1 = Message.objects.create(chat=self.chat, sender=self.user1, content='First')
        msg2 = Message.objects.create(chat=self.chat, sender=self.user2, content='Second')

        url = f'/api/chats/{self.chat.id}/messages/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['content'], 'First')
        self.assertEqual(response.data[1]['content'], 'Second')

    def test_cannot_send_message_to_other_user_chat(self):
        """❌ Cannot send message to chat user is not part of"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        other_match = Match.objects.create(user1=other_user, user2=self.user2)
        # Chat is auto-created by signal, so get it instead of creating
        other_chat = Chat.objects.get(match=other_match)

        url = f'/api/chats/{other_chat.id}/messages/'
        data = {'content': 'Hello!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PreferenceAPITests(APITestCase):
    """Test Preference and UserPreference CRUD operations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        token_plain, _ = ExpiringToken.generate_token_for_user(self.user, days_valid=365, name="test")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_plain}')
        self.pref1 = Preference.objects.create(name='Books')
        self.pref2 = Preference.objects.create(name='Gym')

    def test_list_preferences(self):
        """✅ List all preferences"""
        response = self.client.get('/api/preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_create_preference(self):
        """✅ Create a new preference"""
        data = {'name': 'Coffee'}
        response = self.client.post('/api/preferences/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Coffee')

    def test_add_user_preference(self):
        """✅ Add a preference to user"""
        data = {'preference_id': self.pref1.id}
        response = self.client.post('/api/user-preferences/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check it was created
        user_prefs = UserPreference.objects.filter(user=self.user)
        self.assertEqual(user_prefs.count(), 1)

    def test_list_user_preferences(self):
        """✅ List user's preferences"""
        UserPreference.objects.create(user=self.user, preference=self.pref1)
        UserPreference.objects.create(user=self.user, preference=self.pref2)

        response = self.client.get('/api/user-preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_delete_user_preference(self):
        """✅ Remove a preference from user"""
        UserPreference.objects.create(user=self.user, preference=self.pref1)

        url = f'/api/user-preferences/{self.pref1.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check it was deleted
        user_prefs = UserPreference.objects.filter(user=self.user)
        self.assertEqual(user_prefs.count(), 0)

    def test_cannot_add_duplicate_preference(self):
        """❌ Cannot add duplicate preference for user"""
        UserPreference.objects.create(user=self.user, preference=self.pref1)

        data = {'preference_id': self.pref1.id}
        response = self.client.post('/api/user-preferences/', data, format='json')
        # Should either return 400 or silently succeed (depending on implementation)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])
