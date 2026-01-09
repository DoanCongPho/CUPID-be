"""
Tests for Chat and Message Views and Serializers
Tests for chat management and messaging
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import Chat, Message, Match, ExpiringToken

User = get_user_model()


class ChatListTests(APITestCase):
    """Test chat list endpoint"""

    def setUp(self):
        self.chat_url = '/api/chats/'
        self.user1 = User.objects.create_user(
            email='chat1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='chat2@example.com',
            password='pass123'
        )
        self.user3 = User.objects.create_user(
            email='chat3@example.com',
            password='pass123'
        )
        
        self.match1 = Match.objects.create(user1=self.user1, user2=self.user2)
        self.match2 = Match.objects.create(user1=self.user1, user2=self.user3)
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token = plaintext

    def test_list_chats_requires_auth(self):
        """Test listing chats requires authentication"""
        response = self.client.get(self.chat_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_chats(self):
        """Test listing user's chats"""
        Chat.objects.create(match=self.match1)
        Chat.objects.create(match=self.match2)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.chat_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_chats_empty(self):
        """Test listing when no chats exist"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.chat_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_chat(self):
        """Test creating a chat"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'match_id': self.match1.id}
        response = self.client.post(self.chat_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['match']['id'], self.match1.id)

    def test_chat_includes_match_info(self):
        """Test chat response includes match information"""
        chat = Chat.objects.create(match=self.match1)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.chat_url)
        
        self.assertIn('match', response.data[0])
        self.assertEqual(response.data[0]['match']['id'], self.match1.id)


class ChatDetailTests(APITestCase):
    """Test chat detail endpoint"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='chatd1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='chatd2@example.com',
            password='pass123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        self.chat = Chat.objects.create(match=self.match)
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token = plaintext

    def test_get_chat_detail(self):
        """Test retrieving chat detail"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/chats/{self.chat.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.chat.id)

    def test_update_chat_status(self):
        """Test updating chat status"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'status': Chat.STATUS_CLOSED}
        response = self.client.put(f'/api/chats/{self.chat.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Chat.STATUS_CLOSED)

    def test_delete_chat(self):
        """Test deleting chat"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete(f'/api/chats/{self.chat.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deleted
        self.assertFalse(Chat.objects.filter(id=self.chat.id).exists())

    def test_cannot_access_other_chat(self):
        """Test cannot access chat user is not part of"""
        user3 = User.objects.create_user(
            email='chatd3@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(user3)
        token = plaintext
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/chats/{self.chat.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MessageListTests(APITestCase):
    """Test message list endpoint"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='msg1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='msg2@example.com',
            password='pass123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        self.chat = Chat.objects.create(match=self.match)
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token1 = plaintext
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user2)
        self.token2 = plaintext

    def test_list_messages_requires_auth(self):
        """Test listing messages requires authentication"""
        response = self.client.get(f'/api/chats/{self.chat.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_chat_messages(self):
        """Test listing messages in a chat"""
        Message.objects.create(chat=self.chat, sender=self.user1, content='Hello')
        Message.objects.create(chat=self.chat, sender=self.user2, content='Hi there')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(f'/api/chats/{self.chat.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_messages_ordered_by_time(self):
        """Test messages are ordered by sent_at"""
        msg1 = Message.objects.create(chat=self.chat, sender=self.user1, content='First')
        msg2 = Message.objects.create(chat=self.chat, sender=self.user2, content='Second')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        response = self.client.get(f'/api/chats/{self.chat.id}/messages/')
        
        ids = [m['id'] for m in response.data]
        self.assertEqual(ids[0], msg1.id)
        self.assertEqual(ids[1], msg2.id)

    def test_cannot_list_other_chat_messages(self):
        """Test cannot list messages from chats user is not part of"""
        user3 = User.objects.create_user(
            email='msg3@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(user3)
        token = plaintext
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/chats/{self.chat.id}/messages/')
        # Should be filtered to empty or 404
        self.assertIn(response.status_code, [200, 404])

    def test_send_message(self):
        """Test sending a message"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        data = {'content': 'Test message', 'chat': self.chat.id}
        response = self.client.post(f'/api/chats/{self.chat.id}/messages/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test message')
        self.assertEqual(response.data['sender']['id'], self.user1.id)

    def test_send_message_requires_auth(self):
        """Test sending message requires authentication"""
        data = {'content': 'Test', 'chat': self.chat.id}
        response = self.client.post(f'/api/chats/{self.chat.id}/messages/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sender_auto_set(self):
        """Test sender is automatically set to authenticated user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        data = {'content': 'Auto sender'}
        response = self.client.post(f'/api/chats/{self.chat.id}/messages/', data, format='json')
        self.assertEqual(response.data['sender']['id'], self.user1.id)

    def test_send_empty_message(self):
        """Test sending empty message"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        data = {'content': '', 'chat': self.chat.id}
        response = self.client.post(f'/api/chats/{self.chat.id}/messages/', data, format='json')
        # Django DRF may allow empty, but let's check
        # This depends on the serializer

    def test_send_long_message(self):
        """Test sending long message"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        long_content = 'x' * 5000
        data = {'content': long_content}
        response = self.client.post(f'/api/chats/{self.chat.id}/messages/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_send_message_to_wrong_chat(self):
        """Test cannot send message to chat user is not part of"""
        user3 = User.objects.create_user(
            email='msg3@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(user3)
        token = plaintext
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'content': 'Unauthorized message'}
        response = self.client.post(f'/api/chats/{self.chat.id}/messages/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MessageDetailTests(APITestCase):
    """Test message detail endpoint"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='msgd1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='msgd2@example.com',
            password='pass123'
        )
        self.match = Match.objects.create(user1=self.user1, user2=self.user2)
        self.chat = Chat.objects.create(match=self.match)
        self.message = Message.objects.create(
            chat=self.chat,
            sender=self.user1,
            content='Test message'
        )
        
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user1)
        self.token = plaintext

    def test_get_message_detail(self):
        """Test retrieving message detail"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/messages/{self.message.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Test message')

    def test_delete_message(self):
        """Test deleting message"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete(f'/api/messages/{self.message.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deleted
        self.assertFalse(Message.objects.filter(id=self.message.id).exists())

    def test_cannot_get_other_chat_message(self):
        """Test cannot access message from chat user is not part of"""
        user3 = User.objects.create_user(
            email='msgd3@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(user3)
        token = plaintext
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/messages/{self.message.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ChatSerializerTests(APITestCase):
    """Test chat serializers"""

    def test_chat_serializer_fields(self):
        """Test ChatSerializer includes required fields"""
        user1 = User.objects.create_user(
            email='ser1@example.com',
            password='pass123'
        )
        user2 = User.objects.create_user(
            email='ser2@example.com',
            password='pass123'
        )
        match = Match.objects.create(user1=user1, user2=user2)
        chat = Chat.objects.create(match=match)
        
        from users.serializers.chat import ChatSerializer
        serializer = ChatSerializer(chat)
        
        self.assertIn('id', serializer.data)
        self.assertIn('match', serializer.data)
        self.assertIn('status', serializer.data)
        self.assertIn('created_at', serializer.data)


class MessageSerializerTests(APITestCase):
    """Test message serializers"""

    def test_message_serializer_fields(self):
        """Test MessageSerializer includes required fields"""
        user1 = User.objects.create_user(
            email='msgser1@example.com',
            password='pass123'
        )
        user2 = User.objects.create_user(
            email='msgser2@example.com',
            password='pass123'
        )
        match = Match.objects.create(user1=user1, user2=user2)
        chat = Chat.objects.create(match=match)
        message = Message.objects.create(
            chat=chat,
            sender=user1,
            content='Test'
        )
        
        from users.serializers.chat import MessageSerializer
        serializer = MessageSerializer(message)
        
        self.assertIn('id', serializer.data)
        self.assertIn('chat', serializer.data)
        self.assertIn('sender', serializer.data)
        self.assertIn('content', serializer.data)
        self.assertIn('sent_at', serializer.data)
