"""
Test utilities and helpers
Common test utilities for the users app tests
"""
from django.contrib.auth import get_user_model
from users.models import (
    ExpiringToken, UserProfile, Preference, UserPreference,
    Match, Quests, Chat, Message, Task, UserModeSettings
)
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class UserFactory:
    """Factory for creating test users"""
    
    @staticmethod
    def create_user(email=None, phone=None, password='testpass123', **profile_kwargs):
        """Create a user with optional profile"""
        if not email and not phone:
            email = f'user_{timezone.now().timestamp()}@example.com'
        
        user = User.objects.create_user(
            email=email or '',
            phone_number=phone,
            password=password
        )
        
        profile_data = {
            'user': user,
            'full_name': profile_kwargs.get('full_name', f'Test User {user.id}'),
            'gender': profile_kwargs.get('gender', 'M'),
            'nickname': profile_kwargs.get('nickname', f'user{user.id}'),
        }
        profile_data.update({k: v for k, v in profile_kwargs.items() 
                            if k not in ['full_name', 'gender', 'nickname']})
        
        UserProfile.objects.create(**profile_data)
        return user

    @staticmethod
    def create_user_with_token(email=None, password='testpass123', **profile_kwargs):
        """Create a user and return with token"""
        user = UserFactory.create_user(email=email, password=password, **profile_kwargs)
        plaintext, token_obj = ExpiringToken.generate_token_for_user(user)
        return user, plaintext, token_obj


class PreferenceFactory:
    """Factory for creating test preferences"""
    
    @staticmethod
    def create_preference(name=None):
        """Create a preference"""
        if not name:
            count = Preference.objects.count()
            name = f'Preference {count + 1}'
        
        pref, _ = Preference.objects.get_or_create(name=name)
        return pref

    @staticmethod
    def create_preferences(names=None):
        """Create multiple preferences"""
        if not names:
            names = ['Books', 'Gym', 'Coffee', 'Hiking', 'Sports']
        
        prefs = []
        for name in names:
            prefs.append(PreferenceFactory.create_preference(name))
        return prefs

    @staticmethod
    def assign_preferences(user, preferences):
        """Assign preferences to a user"""
        for pref in preferences:
            UserPreference.objects.get_or_create(user=user, preference=pref)


class MatchFactory:
    """Factory for creating test matches"""
    
    @staticmethod
    def create_match(user1=None, user2=None, status=None):
        """Create a match between two users"""
        if not user1:
            user1 = UserFactory.create_user()
        if not user2:
            user2 = UserFactory.create_user()
        
        return Match.objects.create(
            user1=user1,
            user2=user2,
            status=status or Match.STATUS_SUCCESSFUL,
            matched_at=timezone.now()
        )

    @staticmethod
    def create_match_with_chat(user1=None, user2=None):
        """Create a match with associated chat"""
        match = MatchFactory.create_match(user1, user2)
        chat = Chat.objects.create(match=match)
        return match, chat


class QuestFactory:
    """Factory for creating test quests"""
    
    @staticmethod
    def create_quest(match=None, activity='Coffee', status=None, **kwargs):
        """Create a quest"""
        if not match:
            match = MatchFactory.create_match()
        
        quest_date = kwargs.get('quest_date', timezone.now().date())
        
        return Quests.objects.create(
            match=match,
            activity=activity,
            quest_date=quest_date,
            status=status or Quests.STATUS_PENDING,
            location_latitude=kwargs.get('latitude', 21.0285),
            location_longitude=kwargs.get('longitude', 105.8542),
            xp_reward=kwargs.get('xp_reward', 0)
        )


class MessageFactory:
    """Factory for creating test messages"""
    
    @staticmethod
    def create_chat_with_messages(user1=None, user2=None, message_count=5):
        """Create chat with messages"""
        if not user1:
            user1 = UserFactory.create_user()
        if not user2:
            user2 = UserFactory.create_user()
        
        match = Match.objects.create(user1=user1, user2=user2)
        chat = Chat.objects.create(match=match)
        
        messages = []
        for i in range(message_count):
            sender = user1 if i % 2 == 0 else user2
            msg = Message.objects.create(
                chat=chat,
                sender=sender,
                content=f'Message {i + 1}'
            )
            messages.append(msg)
        
        return chat, messages


class TaskFactory:
    """Factory for creating test tasks"""
    
    @staticmethod
    def create_task(user=None, description=None, **kwargs):
        """Create a task"""
        if not user:
            user = UserFactory.create_user()
        
        if not description:
            count = Task.objects.filter(user=user).count()
            description = f'Task {count + 1}'
        
        return Task.objects.create(
            user=user,
            description=description,
            scheduled_start_time=kwargs.get('start_time'),
            scheduled_end_time=kwargs.get('end_time'),
            is_free=kwargs.get('is_free', False)
        )

    @staticmethod
    def create_tasks_with_schedule(user=None, count=3):
        """Create multiple tasks with schedules"""
        if not user:
            user = UserFactory.create_user()
        
        tasks = []
        for i in range(count):
            start = timezone.now() + timedelta(days=i)
            end = start + timedelta(hours=2)
            task = Task.objects.create(
                user=user,
                description=f'Scheduled task {i + 1}',
                scheduled_start_time=start,
                scheduled_end_time=end
            )
            tasks.append(task)
        
        return tasks


class AuthTestMixin:
    """Mixin for authentication testing"""
    
    def create_authenticated_client(self, user=None, **user_kwargs):
        """Create a client with authenticated user"""
        if not user:
            user = UserFactory.create_user(**user_kwargs)
        
        plaintext, _ = ExpiringToken.generate_token_for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {plaintext}')
        return self.client, user, plaintext

    def login_as(self, user):
        """Login as a specific user"""
        plaintext, _ = ExpiringToken.generate_token_for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {plaintext}')
        return plaintext


def create_test_data_set():
    """Create a comprehensive test dataset"""
    # Create users
    user1, token1, _ = UserFactory.create_user_with_token(email='test1@example.com')
    user2, token2, _ = UserFactory.create_user_with_token(email='test2@example.com')
    user3, token3, _ = UserFactory.create_user_with_token(email='test3@example.com')
    
    # Create preferences
    prefs = PreferenceFactory.create_preferences()
    PreferenceFactory.assign_preferences(user1, prefs[:2])
    PreferenceFactory.assign_preferences(user2, prefs[1:3])
    
    # Create matches
    match1 = MatchFactory.create_match(user1, user2)
    match2 = MatchFactory.create_match(user2, user3)
    
    # Create chats and messages
    chat1 = Chat.objects.create(match=match1)
    Message.objects.create(chat=chat1, sender=user1, content='Hi user2')
    Message.objects.create(chat=chat1, sender=user2, content='Hi user1')
    
    # Create quests
    quest1 = QuestFactory.create_quest(match1, activity='Coffee')
    quest2 = QuestFactory.create_quest(match2, activity='Dinner')
    
    # Create tasks
    TaskFactory.create_task(user1, 'Shopping')
    TaskFactory.create_task(user2, 'Work')
    
    # Create settings
    UserModeSettings.objects.create(user=user1)
    UserModeSettings.objects.create(user=user2)
    
    return {
        'users': {'user1': user1, 'user2': user2, 'user3': user3},
        'tokens': {'token1': token1, 'token2': token2, 'token3': token3},
        'preferences': prefs,
        'matches': {'match1': match1, 'match2': match2},
        'chats': {'chat1': chat1},
        'quests': {'quest1': quest1, 'quest2': quest2}
    }
