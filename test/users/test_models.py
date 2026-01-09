"""
Tests for User Models
Tests for User, UserProfile, UserModeSettings, Preference, UserPreference models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from users.models import (
    UserProfile, UserModeSettings, Preference, UserPreference,
    Match, Quests, Chat, Message, ExpiringToken, Task
)

User = get_user_model()


class UserModelTests(TestCase):
    """Test custom User model"""

    def test_create_user_with_email(self):
        """Test creating a user with email"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))

    def test_create_user_with_phone(self):
        """Test creating a user with phone number"""
        user = User.objects.create_user(
            email="phone@example.com",
            phone_number="+84901234567",
            password="testpass123"
        )
        self.assertEqual(user.phone_number, "+84901234567")

    def test_user_str_representation(self):
        """Test User string representation"""
        user = User.objects.create_user(
            email="str@example.com",
            password="testpass123"
        )
        self.assertEqual(str(user), "str@example.com")

    def test_user_with_provider(self):
        """Test user with external provider"""
        user = User.objects.create_user(
            email="oauth@example.com",
            password="testpass123",
            provider="google",
            provider_id="google123"
        )
        self.assertEqual(user.provider, "google")
        self.assertEqual(user.provider_id, "google123")

    def test_user_timestamps(self):
        """Test user creation and update timestamps"""
        user = User.objects.create_user(
            email="timestamp@example.com",
            password="testpass123"
        )
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)


class UserProfileTests(TestCase):
    """Test UserProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="testpass123"
        )

    def test_create_profile(self):
        """Test creating a user profile"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name="John Doe",
            nickname="john",
            gender="M"
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.full_name, "John Doe")

    def test_profile_one_to_one_with_user(self):
        """Test OneToOne relationship with User"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name="Jane Doe"
        )
        # Accessing through reverse relation
        self.assertEqual(self.user.profile, profile)

    def test_profile_default_values(self):
        """Test profile default values"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertFalse(profile.is_verified)
        self.assertEqual(profile.total_xp, 0)
        self.assertFalse(profile.is_matched)

    def test_profile_with_coordinates(self):
        """Test profile with home coordinates"""
        profile = UserProfile.objects.create(
            user=self.user,
            home_latitude=21.0285,
            home_longitude=105.8542
        )
        self.assertEqual(profile.home_latitude, 21.0285)
        self.assertEqual(profile.home_longitude, 105.8542)

    def test_profile_with_service_account(self):
        """Test service account marking"""
        profile = UserProfile.objects.create(
            user=self.user,
            is_service_account=True
        )
        self.assertTrue(profile.is_service_account)

    def test_profile_str_representation(self):
        """Test UserProfile string representation"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertIn(self.user.username, str(profile))


class UserModeSettingsTests(TestCase):
    """Test UserModeSettings model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="settings@example.com",
            password="testpass123"
        )

    def test_create_settings(self):
        """Test creating user settings"""
        settings = UserModeSettings.objects.create(user=self.user)
        self.assertIsNotNone(settings)

    def test_settings_defaults(self):
        """Test default values for settings"""
        settings = UserModeSettings.objects.create(user=self.user)
        self.assertFalse(settings.ghost_mode_enabled)
        self.assertTrue(settings.daily_reminders_enabled)
        self.assertTrue(settings.location_sharing_enabled)
        self.assertTrue(settings.spotmatch_notifications_enabled)

    def test_modify_settings(self):
        """Test modifying user settings"""
        settings = UserModeSettings.objects.create(user=self.user)
        settings.ghost_mode_enabled = True
        settings.daily_reminders_enabled = False
        settings.save()
        
        updated = UserModeSettings.objects.get(user=self.user)
        self.assertTrue(updated.ghost_mode_enabled)
        self.assertFalse(updated.daily_reminders_enabled)

    def test_settings_one_to_one(self):
        """Test OneToOne relationship"""
        settings = UserModeSettings.objects.create(user=self.user)
        self.assertEqual(self.user.settings, settings)


class PreferenceTests(TestCase):
    """Test Preference model"""

    def test_create_preference(self):
        """Test creating a preference"""
        pref = Preference.objects.create(name="Books")
        self.assertEqual(pref.name, "Books")

    def test_preference_unique_name(self):
        """Test preference name uniqueness"""
        Preference.objects.create(name="Gym")
        with self.assertRaises(Exception):
            Preference.objects.create(name="Gym")

    def test_preference_ordering(self):
        """Test preferences are ordered by name"""
        Preference.objects.create(name="Hiking")
        Preference.objects.create(name="Books")
        Preference.objects.create(name="Coffee")
        
        prefs = list(Preference.objects.all())
        names = [p.name for p in prefs]
        self.assertEqual(names, ["Books", "Coffee", "Hiking"])

    def test_preference_str_representation(self):
        """Test Preference string representation"""
        pref = Preference.objects.create(name="Sports")
        self.assertEqual(str(pref), "Sports")


class UserPreferenceTests(TestCase):
    """Test UserPreference model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="prefs@example.com",
            password="testpass123"
        )
        self.pref1 = Preference.objects.create(name="Books")
        self.pref2 = Preference.objects.create(name="Gym")

    def test_create_user_preference(self):
        """Test creating user preference"""
        up = UserPreference.objects.create(
            user=self.user,
            preference=self.pref1
        )
        self.assertEqual(up.user, self.user)
        self.assertEqual(up.preference, self.pref1)

    def test_user_preference_unique_together(self):
        """Test unique constraint on (user, preference)"""
        UserPreference.objects.create(user=self.user, preference=self.pref1)
        with self.assertRaises(Exception):
            UserPreference.objects.create(user=self.user, preference=self.pref1)

    def test_user_multiple_preferences(self):
        """Test user can have multiple preferences"""
        UserPreference.objects.create(user=self.user, preference=self.pref1)
        UserPreference.objects.create(user=self.user, preference=self.pref2)
        
        prefs = UserPreference.objects.filter(user=self.user)
        self.assertEqual(prefs.count(), 2)

    def test_user_preference_cascade_delete(self):
        """Test preferences deleted when user is deleted"""
        UserPreference.objects.create(user=self.user, preference=self.pref1)
        user_id = self.user.id
        self.user.delete()
        
        prefs = UserPreference.objects.filter(user_id=user_id)
        self.assertEqual(prefs.count(), 0)


class MatchTests(TestCase):
    """Test Match model"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="testpass123"
        )

    def test_create_match(self):
        """Test creating a match between two users"""
        match = Match.objects.create(
            user1=self.user1,
            user2=self.user2,
            status=Match.STATUS_SUCCESSFUL
        )
        self.assertEqual(match.user1, self.user1)
        self.assertEqual(match.user2, self.user2)

    def test_match_status_choices(self):
        """Test match status choices"""
        statuses = [
            Match.STATUS_SUCCESSFUL,
            Match.STATUS_USER1_MISSED,
            Match.STATUS_USER2_MISSED,
            Match.STATUS_EXPIRED
        ]
        for status in statuses:
            match = Match.objects.create(
                user1=self.user1,
                user2=self.user2,
                status=status
            )
            self.assertEqual(match.status, status)

    def test_match_ratings(self):
        """Test match ratings"""
        match = Match.objects.create(
            user1=self.user1,
            user2=self.user2,
            user1_rating=4,
            user2_rating=5
        )
        self.assertEqual(match.user1_rating, 4)
        self.assertEqual(match.user2_rating, 5)

    def test_match_timestamp(self):
        """Test match timestamp"""
        now = timezone.now()
        match = Match.objects.create(
            user1=self.user1,
            user2=self.user2,
            matched_at=now
        )
        self.assertEqual(match.matched_at, now)

    def test_match_str_representation(self):
        """Test Match string representation"""
        match = Match.objects.create(
            user1=self.user1,
            user2=self.user2,
            status=Match.STATUS_SUCCESSFUL
        )
        self.assertIn(str(self.user1.id), str(match))


class QuestTests(TestCase):
    """Test Quests model"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="testpass123"
        )
        self.match = Match.objects.create(
            user1=self.user1,
            user2=self.user2
        )

    def test_create_quest(self):
        """Test creating a quest"""
        quest = Quests.objects.create(
            match=self.match,
            activity="Coffee",
            quest_date="2025-01-10",
            status=Quests.STATUS_PENDING
        )
        self.assertEqual(quest.match, self.match)
        self.assertEqual(quest.activity, "Coffee")

    def test_quest_with_location(self):
        """Test quest with location coordinates"""
        quest = Quests.objects.create(
            match=self.match,
            location_name="Café X",
            activity="Coffee",
            quest_date="2025-01-10",
            location_latitude=21.0285,
            location_longitude=105.8542
        )
        self.assertEqual(quest.location_latitude, 21.0285)

    def test_quest_status_choices(self):
        """Test quest status choices"""
        for status in [Quests.STATUS_PENDING, Quests.STATUS_COMPLETED]:
            quest = Quests.objects.create(
                match=self.match,
                activity="Activity",
                quest_date="2025-01-10",
                status=status
            )
            self.assertEqual(quest.status, status)

    def test_quest_unique_together(self):
        """Test unique constraint on (match, location_name)"""
        Quests.objects.create(
            match=self.match,
            location_name="Café X",
            activity="Coffee",
            quest_date="2025-01-10"
        )
        with self.assertRaises(Exception):
            Quests.objects.create(
                match=self.match,
                location_name="Café X",
                activity="Different",
                quest_date="2025-01-11"
            )

    def test_quest_with_hints(self):
        """Test quest with hints from both users"""
        quest = Quests.objects.create(
            match=self.match,
            activity="Coffee",
            quest_date="2025-01-10",
            hint_user1="Near subway",
            hint_user2="Has wifi"
        )
        self.assertEqual(quest.hint_user1, "Near subway")
        self.assertEqual(quest.hint_user2, "Has wifi")

    def test_quest_xp_reward(self):
        """Test quest XP reward"""
        quest = Quests.objects.create(
            match=self.match,
            activity="Coffee",
            quest_date="2025-01-10",
            xp_reward=100
        )
        self.assertEqual(quest.xp_reward, 100)


class ChatTests(TestCase):
    """Test Chat model"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="testpass123"
        )
        self.match = Match.objects.create(
            user1=self.user1,
            user2=self.user2
        )

    def test_create_chat(self):
        """Test creating a chat"""
        chat = Chat.objects.create(
            match=self.match,
            status=Chat.STATUS_ACTIVE
        )
        self.assertEqual(chat.match, self.match)

    def test_chat_status_choices(self):
        """Test chat status choices"""
        for status in [Chat.STATUS_ACTIVE, Chat.STATUS_CLOSED]:
            chat = Chat.objects.create(
                match=self.match,
                status=status
            )
            self.assertEqual(chat.status, status)

    def test_chat_one_to_one_with_match(self):
        """Test OneToOne relationship with Match"""
        chat = Chat.objects.create(match=self.match)
        self.assertEqual(self.match.chat, chat)

    def test_chat_str_representation(self):
        """Test Chat string representation"""
        chat = Chat.objects.create(match=self.match)
        self.assertIn(str(self.match.id), str(chat))


class MessageTests(TestCase):
    """Test Message model"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="testpass123"
        )
        self.match = Match.objects.create(
            user1=self.user1,
            user2=self.user2
        )
        self.chat = Chat.objects.create(match=self.match)

    def test_create_message(self):
        """Test creating a message"""
        msg = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            content="Hello!"
        )
        self.assertEqual(msg.chat, self.chat)
        self.assertEqual(msg.sender, self.user1)
        self.assertEqual(msg.content, "Hello!")

    def test_message_ordering(self):
        """Test messages are ordered by sent_at"""
        msg1 = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            content="First"
        )
        msg2 = Message.objects.create(
            chat=self.chat,
            sender=self.user2,
            content="Second"
        )
        messages = list(Message.objects.all())
        self.assertEqual(messages[0].id, msg1.id)
        self.assertEqual(messages[1].id, msg2.id)

    def test_message_cascade_delete(self):
        """Test messages deleted when chat is deleted"""
        Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            content="Test"
        )
        chat_id = self.chat.id
        self.chat.delete()
        
        messages = Message.objects.filter(chat_id=chat_id)
        self.assertEqual(messages.count(), 0)


class TaskTests(TestCase):
    """Test Task model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="task@example.com",
            password="testpass123"
        )

    def test_create_task(self):
        """Test creating a task"""
        task = Task.objects.create(
            user=self.user,
            description="Buy groceries"
        )
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.description, "Buy groceries")

    def test_task_with_schedule(self):
        """Test task with scheduled times"""
        start = timezone.now()
        end = start + timedelta(hours=2)
        task = Task.objects.create(
            user=self.user,
            description="Meeting",
            scheduled_start_time=start,
            scheduled_end_time=end
        )
        self.assertEqual(task.scheduled_start_time, start)
        self.assertEqual(task.scheduled_end_time, end)

    def test_task_is_free(self):
        """Test task is_free field"""
        task = Task.objects.create(
            user=self.user,
            description="Free time",
            is_free=True
        )
        self.assertTrue(task.is_free)

    def test_task_cascade_delete(self):
        """Test tasks deleted when user is deleted"""
        Task.objects.create(user=self.user, description="Test")
        user_id = self.user.id
        self.user.delete()
        
        tasks = Task.objects.filter(user_id=user_id)
        self.assertEqual(tasks.count(), 0)


class ExpiringTokenTests(TestCase):
    """Test ExpiringToken model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="token@example.com",
            password="testpass123"
        )

    def test_generate_token(self):
        """Test generating a token"""
        plaintext, token_obj = ExpiringToken.generate_token_for_user(self.user)
        self.assertIsNotNone(plaintext)
        self.assertEqual(token_obj.user, self.user)
        self.assertFalse(token_obj.revoked)

    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user)
        verified = ExpiringToken.verify_token(plaintext)
        self.assertIsNotNone(verified)
        self.assertEqual(verified.user, self.user)

    def test_verify_revoked_token(self):
        """Test verifying a revoked token returns None"""
        plaintext, token_obj = ExpiringToken.generate_token_for_user(self.user)
        token_obj.revoke()
        verified = ExpiringToken.verify_token(plaintext)
        self.assertIsNone(verified)

    def test_verify_expired_token(self):
        """Test verifying an expired token returns None"""
        plaintext, token_obj = ExpiringToken.generate_token_for_user(self.user)
        token_obj.expires_at = timezone.now() - timedelta(hours=1)
        token_obj.save()
        verified = ExpiringToken.verify_token(plaintext)
        self.assertIsNone(verified)

    def test_token_with_name(self):
        """Test token with custom name"""
        plaintext, token_obj = ExpiringToken.generate_token_for_user(
            self.user,
            name="api-key"
        )
        self.assertEqual(token_obj.name, "api-key")

    def test_token_hash_is_stored(self):
        """Test that plaintext token is not stored, only hash"""
        plaintext, token_obj = ExpiringToken.generate_token_for_user(self.user)
        self.assertNotEqual(token_obj.key_hash, plaintext)
        self.assertTrue(len(token_obj.key_hash) == 64)  # SHA256 hex length

    def test_revoke_token(self):
        """Test revoking a token"""
        plaintext, token_obj = ExpiringToken.generate_token_for_user(self.user)
        token_obj.revoke()
        
        updated = ExpiringToken.objects.get(pk=token_obj.pk)
        self.assertTrue(updated.revoked)
