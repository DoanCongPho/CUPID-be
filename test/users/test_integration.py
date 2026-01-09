"""
Integration tests for the users app
Tests that verify multiple components working together
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from users.models import (
    UserProfile, ExpiringToken, Preference, UserPreference,
    Match, Quests, Chat, Message, Task, UserModeSettings
)
from test.users.test_utils import (
    UserFactory, PreferenceFactory, MatchFactory,
    QuestFactory, TaskFactory, create_test_data_set, AuthTestMixin
)

User = get_user_model()


class UserRegistrationAndLoginIntegrationTests(APITestCase):
    """Integration tests for registration and login flow"""

    def test_full_registration_flow(self):
        """Test complete registration flow with profile and preferences"""
        # Create preferences first
        pref1 = PreferenceFactory.create_preference('Books')
        pref2 = PreferenceFactory.create_preference('Gym')
        
        # Register with all data
        data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'full_name': 'New User',
            'gender': 'F',
            'nickname': 'newuser',
            'date_of_birth': '1995-05-15',
            'home_latitude': 21.0285,
            'home_longitude': 105.8542,
            'preferences': [pref1.id, pref2.id]
        }
        
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user created
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.email, 'newuser@example.com')
        
        # Verify profile created with data
        profile = user.profile
        self.assertEqual(profile.full_name, 'New User')
        self.assertEqual(profile.gender, 'F')
        self.assertEqual(profile.home_latitude, 21.0285)
        
        # Verify preferences assigned
        prefs = UserPreference.objects.filter(user=user)
        self.assertEqual(prefs.count(), 2)

    def test_registration_login_flow(self):
        """Test registering then logging in"""
        # Register
        register_data = {
            'email': 'flow@example.com',
            'password': 'flowpass123',
            'full_name': 'Flow User'
        }
        response = self.client.post('/api/auth/register/', register_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Login
        login_data = {
            'email': 'flow@example.com',
            'password': 'flowpass123'
        }
        response = self.client.post('/api/auth/login/', login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_then_update_profile(self):
        """Test logging in and updating profile"""
        user = UserFactory.create_user(email='update@example.com')
        
        # Login
        plaintext, _ = ExpiringToken.generate_token_for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {plaintext}')
        
        # Update profile
        data = {'full_name': 'Updated Name'}
        response = self.client.put('/api/profile/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify updated
        user.refresh_from_db()
        self.assertEqual(user.profile.full_name, 'Updated Name')


class MatchAndQuestIntegrationTests(APITestCase):
    """Integration tests for matching and quest flow"""

    def test_create_match_and_quest(self):
        """Test creating match then quest"""
        user1, token1, _ = UserFactory.create_user_with_token()
        user2, token2, _ = UserFactory.create_user_with_token()
        
        # Create match
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        match_data = {'user2_id': user2.id}
        match_response = self.client.post('/api/matches/', match_data, format='json')
        match_id = match_response.data['id']
        
        # Create quest for match
        quest_data = {
            'match_id': match_id,
            'activity': 'Coffee',
            'location_name': 'Café X',
            'quest_date': '2025-01-20'
        }
        quest_response = self.client.post('/api/quests/', quest_data, format='json')
        self.assertEqual(quest_response.status_code, status.HTTP_201_CREATED)

    def test_match_quest_and_hint_flow(self):
        """Test creating match, quest, and posting hints"""
        user1, token1, _ = UserFactory.create_user_with_token()
        user2, token2, _ = UserFactory.create_user_with_token()
        
        # Create match
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        match_data = {'user2_id': user2.id}
        match_response = self.client.post('/api/matches/', match_data, format='json')
        match_id = match_response.data['id']
        
        # Create quest
        quest_data = {
            'match_id': match_id,
            'activity': 'Dinner',
            'quest_date': '2025-01-20'
        }
        quest_response = self.client.post('/api/quests/', quest_data, format='json')
        quest_id = quest_response.data['id']
        
        # User1 posts hint
        hint_data = {'hint': 'Near the park'}
        self.client.post(f'/api/quests/{quest_id}/hint/', hint_data, format='json')
        
        # User2 posts hint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        hint_data = {'hint': 'Has good wifi'}
        hint_response = self.client.post(f'/api/quests/{quest_id}/hint/', hint_data, format='json')
        self.assertEqual(hint_response.status_code, status.HTTP_200_OK)

    def test_match_and_rating_flow(self):
        """Test creating match and rating"""
        user1, token1, _ = UserFactory.create_user_with_token()
        user2, token2, _ = UserFactory.create_user_with_token()
        
        match = MatchFactory.create_match(user1, user2)
        
        # User1 rates
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        response = self.client.post(f'/api/matches/{match.id}/rate/', {'rating': 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User2 rates
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        response = self.client.post(f'/api/matches/{match.id}/rate/', {'rating': 4}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChatAndMessagingIntegrationTests(APITestCase):
    """Integration tests for chat and messaging"""

    def test_create_match_chat_and_message(self):
        """Test creating match, chat, and messaging"""
        user1, token1, _ = UserFactory.create_user_with_token()
        user2, token2, _ = UserFactory.create_user_with_token()
        
        # Create match
        match = MatchFactory.create_match(user1, user2)
        
        # Create chat
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        chat_data = {'match_id': match.id}
        chat_response = self.client.post('/api/chats/', chat_data, format='json')
        chat_id = chat_response.data['id']
        
        # User1 sends message
        msg_data = {'content': 'Hello!'}
        msg_response = self.client.post(f'/api/chats/{chat_id}/messages/', msg_data, format='json')
        self.assertEqual(msg_response.status_code, status.HTTP_201_CREATED)
        
        # User2 sends message
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        msg_data = {'content': 'Hi there!'}
        msg_response = self.client.post(f'/api/chats/{chat_id}/messages/', msg_data, format='json')
        self.assertEqual(msg_response.status_code, status.HTTP_201_CREATED)
        
        # List messages
        msg_list_response = self.client.get(f'/api/chats/{chat_id}/messages/')
        self.assertEqual(len(msg_list_response.data), 2)

    def test_conversation_flow(self):
        """Test a realistic conversation flow"""
        user1, token1, _ = UserFactory.create_user_with_token()
        user2, token2, _ = UserFactory.create_user_with_token()
        
        match = MatchFactory.create_match(user1, user2)
        chat = Chat.objects.create(match=match)
        
        # User1 starts conversation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        self.client.post(f'/api/chats/{chat.id}/messages/', 
                        {'content': 'Hey, want to grab coffee?'}, format='json')
        
        # User2 responds
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        self.client.post(f'/api/chats/{chat.id}/messages/', 
                        {'content': 'Sure! When?'}, format='json')
        
        # User1 responds
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        self.client.post(f'/api/chats/{chat.id}/messages/', 
                        {'content': 'Tomorrow at 3pm?'}, format='json')
        
        # Check conversation history
        response = self.client.get(f'/api/chats/{chat.id}/messages/')
        self.assertEqual(len(response.data), 3)


class PreferencesAndMatchingIntegrationTests(APITestCase):
    """Integration tests for preferences and matching"""

    def test_register_with_preferences_and_view(self):
        """Test registering with preferences and viewing them"""
        prefs = PreferenceFactory.create_preferences(['Books', 'Travel'])
        
        # Register with preferences
        data = {
            'email': 'pref@example.com',
            'password': 'prefpass123',
            'preferences': [prefs[0].id, prefs[1].id]
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        
        user = User.objects.get(email='pref@example.com')
        plaintext, _ = ExpiringToken.generate_token_for_user(user)
        
        # View preferences
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {plaintext}')
        response = self.client.get('/api/user-preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_add_remove_preferences(self):
        """Test adding and removing preferences"""
        user = UserFactory.create_user()
        prefs = PreferenceFactory.create_preferences(['Sports', 'Music', 'Art'])
        
        plaintext, _ = ExpiringToken.generate_token_for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {plaintext}')
        
        # Add preference
        self.client.post('/api/user-preferences/', 
                        {'preference_id': prefs[0].id}, format='json')
        
        # Add another
        self.client.post('/api/user-preferences/', 
                        {'preference_id': prefs[1].id}, format='json')
        
        # Check we have 2
        response = self.client.get('/api/user-preferences/')
        self.assertEqual(len(response.data), 2)
        
        # Remove one
        self.client.delete(f'/api/user-preferences/{prefs[0].id}/')
        
        # Check we have 1
        response = self.client.get('/api/user-preferences/')
        self.assertEqual(len(response.data), 1)


class TaskAndSettingsIntegrationTests(APITestCase):
    """Integration tests for tasks and settings"""

    def test_create_tasks_and_settings(self):
        """Test creating tasks and configuring settings"""
        user, token, _ = UserFactory.create_user_with_token()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Create task
        task_data = {
            'description': 'Complete project',
            'is_free': False
        }
        task_response = self.client.post('/api/tasks/', task_data, format='json')
        self.assertEqual(task_response.status_code, status.HTTP_201_CREATED)
        
        # Update settings
        settings_data = {
            'ghost_mode_enabled': True,
            'location_sharing_enabled': False
        }
        settings_response = self.client.put('/api/settings/', settings_data, format='json')
        self.assertEqual(settings_response.status_code, status.HTTP_200_OK)

    def test_tasks_with_schedule_integration(self):
        """Test creating scheduled tasks and managing them"""
        from django.utils import timezone
        from datetime import timedelta
        
        user, token, _ = UserFactory.create_user_with_token()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Create scheduled task
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        
        task_data = {
            'description': 'Team meeting',
            'scheduled_start_time': start.isoformat(),
            'scheduled_end_time': end.isoformat()
        }
        response = self.client.post('/api/tasks/', task_data, format='json')
        task_id = response.data['id']
        
        # Update task
        task_data['description'] = 'Updated meeting'
        response = self.client.put(f'/api/tasks/{task_id}/', task_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # List tasks
        response = self.client.get('/api/tasks/')
        self.assertGreaterEqual(len(response.data), 1)


class CompleteUserJourneyIntegrationTests(APITestCase, AuthTestMixin):
    """Integration tests for complete user journey"""

    def test_complete_user_journey(self):
        """Test a complete user journey from registration to matching"""
        # User 1 registers
        reg_data1 = {
            'email': 'journey1@example.com',
            'password': 'journey123',
            'full_name': 'Journey User 1',
            'gender': 'M',
            'home_latitude': 21.0285,
            'home_longitude': 105.8542
        }
        self.client.post('/api/auth/register/', reg_data1, format='json')
        user1 = User.objects.get(email='journey1@example.com')
        
        # User 2 registers
        reg_data2 = {
            'email': 'journey2@example.com',
            'password': 'journey123',
            'full_name': 'Journey User 2',
            'gender': 'F',
            'home_latitude': 21.0285,
            'home_longitude': 105.8542
        }
        self.client.post('/api/auth/register/', reg_data2, format='json')
        user2 = User.objects.get(email='journey2@example.com')
        
        # User1 logs in and creates match
        plaintext1, _ = ExpiringToken.generate_token_for_user(user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {plaintext1}')
        
        match_response = self.client.post('/api/matches/', 
                                         {'user2_id': user2.id}, format='json')
        match_id = match_response.data['id']
        
        # User1 creates quest
        quest_data = {
            'match_id': match_id,
            'activity': 'Coffee',
            'location_name': 'Café Central',
            'quest_date': '2025-01-25'
        }
        quest_response = self.client.post('/api/quests/', quest_data, format='json')
        quest_id = quest_response.data['id']
        
        # User1 creates chat and sends message
        chat_response = self.client.post('/api/chats/', {'match_id': match_id}, format='json')
        chat_id = chat_response.data['id']
        
        self.client.post(f'/api/chats/{chat_id}/messages/', 
                        {'content': 'Hello! Ready for our adventure?'}, format='json')
        
        # User2 logs in
        plaintext2, _ = ExpiringToken.generate_token_for_user(user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {plaintext2}')
        
        # User2 sees the message
        messages_response = self.client.get(f'/api/chats/{chat_id}/messages/')
        self.assertEqual(len(messages_response.data), 1)
        
        # User2 posts hint
        self.client.post(f'/api/quests/{quest_id}/hint/', 
                        {'hint': 'I love this place!'}, format='json')
        
        # User2 sends reply
        self.client.post(f'/api/chats/{chat_id}/messages/', 
                        {'content': 'Yes! See you there!'}, format='json')
        
        # Verify messages
        messages_response = self.client.get(f'/api/chats/{chat_id}/messages/')
        self.assertEqual(len(messages_response.data), 2)
        
        # Both rate the match
        self.client.post(f'/api/matches/{match_id}/rate/', {'rating': 5}, format='json')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {plaintext1}')
        self.client.post(f'/api/matches/{match_id}/rate/', {'rating': 5}, format='json')
        
        # Verify match ratings
        match_response = self.client.get(f'/api/matches/{match_id}/')
        self.assertEqual(match_response.data['user1_rating'], 5)
        self.assertEqual(match_response.data['user2_rating'], 5)
