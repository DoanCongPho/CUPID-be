"""
Tests for Match and Quest Views and Serializers
Tests for match creation, quest management, and ratings
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from users.models import (
    Match, Quests, ExpiringToken, UserProfile,
    Preference, UserPreference
)

User = get_user_model()


class MatchListTests(APITestCase):
    """Test match list endpoint"""

    def setUp(self):
        self.match_url = '/api/matches/'
        self.user1 = User.objects.create_user(
            email='match1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='match2@example.com',
            password='pass123'
        )
        self.user3 = User.objects.create_user(
            email='match3@example.com',
            password='pass123'
        )
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token1 = plaintext

    def test_list_matches_requires_auth(self):
        """Test listing matches requires authentication"""
        response = self.client.get(self.match_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_matches(self):
        """Test listing user's matches"""
        Match.objects.create(user1=self.user1, user2=self.user2)
        Match.objects.create(user1=self.user1, user2=self.user3)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(self.match_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_matches_both_directions(self):
        """Test matches appear regardless of direction"""
        Match.objects.create(user1=self.user1, user2=self.user2)
        Match.objects.create(user1=self.user3, user2=self.user1)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(self.match_url)
        self.assertEqual(len(response.data), 2)

    def test_create_match(self):
        """Test creating a match"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        data = {'user2_id': self.user2.id}
        response = self.client.post(self.match_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user2']['id'], self.user2.id)

    def test_cannot_match_with_self(self):
        """Test cannot match with self"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        data = {'user2_id': self.user1.id}
        response = self.client.post(self.match_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_match_user1_auto_set(self):
        """Test user1 is automatically set to authenticated user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        data = {'user2_id': self.user2.id}
        response = self.client.post(self.match_url, data, format='json')
        
        self.assertEqual(response.data['user1']['id'], self.user1.id)


class MatchDetailTests(APITestCase):
    """Test match detail endpoint"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='detail1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='detail2@example.com',
            password='pass123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token = plaintext

    def test_get_match_detail(self):
        """Test retrieving match detail"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/matches/{self.match.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.match.id)

    def test_cannot_get_other_user_match(self):
        """Test cannot get match user is not part of"""
        user3 = User.objects.create_user(
            email='detail3@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(user3)
        token = plaintext
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/matches/{self.match.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_match(self):
        """Test updating match"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'status': Match.STATUS_EXPIRED}
        response = self.client.put(f'/api/matches/{self.match.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Match.STATUS_EXPIRED)

    def test_delete_match(self):
        """Test deleting match"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete(f'/api/matches/{self.match.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deleted
        self.assertFalse(Match.objects.filter(id=self.match.id).exists())


class MatchWithUserViewTests(APITestCase):
    """Test match-with-user endpoint"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='mwu1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='mwu2@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token = plaintext

    def test_create_match_with_user(self):
        """Test creating match with specific user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.put(f'/api/matches/with/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_existing_match_with_user(self):
        """Test retrieving existing match returns existing"""
        match = Match.objects.create(user1=self.user1, user2=self.user2)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.put(f'/api/matches/with/{self.user2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], match.id)

    def test_cannot_match_with_self(self):
        """Test cannot match with self"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.put(f'/api/matches/with/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_match_with_nonexistent_user(self):
        """Test matching with nonexistent user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.put(f'/api/matches/with/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuestListTests(APITestCase):
    """Test quest list endpoint"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='quest1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='quest2@example.com',
            password='pass123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token = plaintext

    def test_list_quests_requires_auth(self):
        """Test listing quests requires authentication"""
        response = self.client.get('/api/quests/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_quests(self):
        """Test listing user's quests"""
        quest = Quests.objects.create(
            match=self.match,
            activity='Coffee',
            quest_date='2025-01-10'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/quests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_quest(self):
        """Test creating a quest"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'match_id': self.match.id,
            'activity': 'Dinner',
            'location_name': 'Restaurant',
            'quest_date': '2025-01-15'
        }
        response = self.client.post('/api/quests/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['activity'], 'Dinner')

    def test_cannot_create_quest_for_other_match(self):
        """Test cannot create quest for unrelated match"""
        user3 = User.objects.create_user(
            email='quest3@example.com',
            password='pass123'
        )
        other_match = Match.objects.create(user1=self.user2, user2=user3)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'match_id': other_match.id,
            'activity': 'Activity',
            'quest_date': '2025-01-15'
        }
        response = self.client.post('/api/quests/', data, format='json')
        # Should fail because user is not part of the match
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class QuestDetailTests(APITestCase):
    """Test quest detail endpoint"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='qd1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='qd2@example.com',
            password='pass123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        self.quest = Quests.objects.create(
            match=self.match,
            activity='Coffee',
            quest_date='2025-01-10'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token = plaintext

    def test_get_quest_detail(self):
        """Test retrieving quest detail"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/quests/{self.quest.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity'], 'Coffee')

    def test_update_quest(self):
        """Test updating quest"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'status': Quests.STATUS_COMPLETED,
            'xp_reward': 100
        }
        response = self.client.put(f'/api/quests/{self.quest.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Quests.STATUS_COMPLETED)

    def test_delete_quest(self):
        """Test deleting quest"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete(f'/api/quests/{self.quest.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deleted
        self.assertFalse(Quests.objects.filter(id=self.quest.id).exists())


class QuestHintViewTests(APITestCase):
    """Test quest hint posting"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='hint1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='hint2@example.com',
            password='pass123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        self.quest = Quests.objects.create(
            match=self.match,
            activity='Coffee',
            quest_date='2025-01-10'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token1 = plaintext
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user2)
        self.token2 = plaintext

    def test_post_hint_user1(self):
        """Test user1 posting hint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        data = {'hint': 'Near subway station'}
        response = self.client.post(f'/api/quests/{self.quest.id}/hint/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['hint_user1'], 'Near subway station')

    def test_post_hint_user2(self):
        """Test user2 posting hint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token2}')
        data = {'hint': 'Has outdoor seating'}
        response = self.client.post(f'/api/quests/{self.quest.id}/hint/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['hint_user2'], 'Has outdoor seating')

    def test_post_hint_empty(self):
        """Test posting empty hint fails"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        data = {'hint': ''}
        response = self.client.post(f'/api/quests/{self.quest.id}/hint/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_hint_unrelated_user(self):
        """Test unrelated user cannot post hint"""
        user3 = User.objects.create_user(
            email='hint3@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(user3)
        token = plaintext
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'hint': 'Hint'}
        response = self.client.post(f'/api/quests/{self.quest.id}/hint/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MatchRatingViewTests(APITestCase):
    """Test match rating endpoint"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='rate1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='rate2@example.com',
            password='pass123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token1 = plaintext
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user2)
        self.token2 = plaintext

    def test_post_rating_user1(self):
        """Test user1 posting rating"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        data = {'rating': 4}
        response = self.client.post(f'/api/matches/{self.match.id}/rate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user1_rating'], 4)

    def test_post_rating_user2(self):
        """Test user2 posting rating"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token2}')
        data = {'rating': 5}
        response = self.client.post(f'/api/matches/{self.match.id}/rate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user2_rating'], 5)

    def test_rating_range(self):
        """Test rating must be 1-5"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # Test too low
        response = self.client.post(f'/api/matches/{self.match.id}/rate/', {'rating': 0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test too high
        response = self.client.post(f'/api/matches/{self.match.id}/rate/', {'rating': 6}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_unrelated_user(self):
        """Test unrelated user cannot rate"""
        user3 = User.objects.create_user(
            email='rate3@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(user3)
        token = plaintext
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/api/matches/{self.match.id}/rate/', {'rating': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rating_missing(self):
        """Test posting without rating"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.post(f'/api/matches/{self.match.id}/rate/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
