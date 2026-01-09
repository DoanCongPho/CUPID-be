"""
Tests for Task Views and Serializers
Tests for task management and user settings
"""
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from users.models import Task, UserModeSettings, ExpiringToken

User = get_user_model()


class TaskListTests(APITestCase):
    """Test task list endpoint"""

    def setUp(self):
        self.task_url = '/api/tasks/'
        self.user = User.objects.create_user(
            email='taskuser@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user)
        self.token = plaintext

    def test_list_tasks_requires_auth(self):
        """Test listing tasks requires authentication"""
        response = self.client.get(self.task_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_tasks(self):
        """Test listing user's tasks"""
        Task.objects.create(user=self.user, description='Task 1')
        Task.objects.create(user=self.user, description='Task 2')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.task_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_only_own_tasks(self):
        """Test user only sees own tasks"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='pass123'
        )
        Task.objects.create(user=self.user, description='My task')
        Task.objects.create(user=other_user, description='Other task')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.task_url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['description'], 'My task')

    def test_create_task(self):
        """Test creating a task"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'description': 'Buy groceries'}
        response = self.client.post(self.task_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Buy groceries')

    def test_create_task_with_schedule(self):
        """Test creating task with schedule"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        start = timezone.now()
        end = start + timedelta(hours=2)
        data = {
            'description': 'Meeting',
            'scheduled_start_time': start.isoformat(),
            'scheduled_end_time': end.isoformat()
        }
        response = self.client.post(self.task_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Meeting')

    def test_create_free_time_task(self):
        """Test creating free time task"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'description': 'Free time',
            'is_free': True
        }
        response = self.client.post(self.task_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_free'])

    def test_task_ordering(self):
        """Test tasks are ordered by creation date (newest first)"""
        import time
        task1 = Task.objects.create(user=self.user, description='First')
        time.sleep(0.1)
        task2 = Task.objects.create(user=self.user, description='Second')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.task_url)
        
        # Newest first
        self.assertEqual(response.data[0]['id'], task2.id)
        self.assertEqual(response.data[1]['id'], task1.id)


class TaskDetailTests(APITestCase):
    """Test task detail endpoint"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='taskdetail@example.com',
            password='pass123'
        )
        self.task = Task.objects.create(
            user=self.user,
            description='Test task'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user)
        self.token = plaintext

    def test_get_task_detail(self):
        """Test retrieving task detail"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Test task')

    def test_update_task(self):
        """Test updating task"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'description': 'Updated task'}
        response = self.client.put(f'/api/tasks/{self.task.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated task')

    def test_update_task_schedule(self):
        """Test updating task schedule"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        start = timezone.now()
        end = start + timedelta(hours=1)
        data = {
            'scheduled_start_time': start.isoformat(),
            'scheduled_end_time': end.isoformat()
        }
        response = self.client.put(f'/api/tasks/{self.task.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_task(self):
        """Test deleting task"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete(f'/api/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deleted
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_cannot_access_other_user_task(self):
        """Test cannot access other user's task"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(other_user)
        token = plaintext
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_requires_auth(self):
        """Test task detail requires authentication"""
        response = self.client.get(f'/api/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserModeSettingsTests(APITestCase):
    """Test user mode settings endpoint"""

    def setUp(self):
        self.settings_url = '/api/settings/'
        self.user = User.objects.create_user(
            email='settings@example.com',
            password='pass123'
        )
        plaintext, _ = ExpiringToken.generate_token_for_user(self.user)
        self.token = plaintext

    def test_get_settings_requires_auth(self):
        """Test getting settings requires authentication"""
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_settings(self):
        """Test retrieving user settings"""
        settings = UserModeSettings.objects.create(user=self.user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ghost_mode_enabled', response.data)

    def test_get_settings_auto_creates(self):
        """Test retrieving settings auto-creates if not exists"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify created in database
        self.assertTrue(UserModeSettings.objects.filter(user=self.user).exists())

    def test_update_settings(self):
        """Test updating user settings"""
        UserModeSettings.objects.create(user=self.user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'ghost_mode_enabled': True,
            'daily_reminders_enabled': False
        }
        response = self.client.put(self.settings_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['ghost_mode_enabled'])
        self.assertFalse(response.data['daily_reminders_enabled'])

    def test_update_location_sharing(self):
        """Test updating location sharing setting"""
        UserModeSettings.objects.create(user=self.user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'location_sharing_enabled': False}
        response = self.client.put(self.settings_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['location_sharing_enabled'])

    def test_update_notifications(self):
        """Test updating notification settings"""
        UserModeSettings.objects.create(user=self.user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'spotmatch_notifications_enabled': False}
        response = self.client.put(self.settings_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['spotmatch_notifications_enabled'])

    def test_partial_settings_update(self):
        """Test partial settings update"""
        settings = UserModeSettings.objects.create(user=self.user)
        original_reminder = settings.daily_reminders_enabled
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {'ghost_mode_enabled': True}
        response = self.client.put(self.settings_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['ghost_mode_enabled'])
        # Original value should be preserved
        self.assertEqual(response.data['daily_reminders_enabled'], original_reminder)

    def test_settings_has_defaults(self):
        """Test settings have correct default values"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.settings_url)
        
        self.assertFalse(response.data['ghost_mode_enabled'])
        self.assertTrue(response.data['daily_reminders_enabled'])
        self.assertTrue(response.data['location_sharing_enabled'])
        self.assertTrue(response.data['spotmatch_notifications_enabled'])


class TaskSerializerTests(APITestCase):
    """Test task serializers"""

    def test_task_serializer_fields(self):
        """Test TaskSerializer includes required fields"""
        user = User.objects.create_user(
            email='serialize@example.com',
            password='pass123'
        )
        task = Task.objects.create(user=user, description='Test')
        
        from users.serializers.task import TaskSerializer
        serializer = TaskSerializer(task)
        
        self.assertIn('id', serializer.data)
        self.assertIn('description', serializer.data)
        self.assertIn('scheduled_start_time', serializer.data)
        self.assertIn('scheduled_end_time', serializer.data)
        self.assertIn('is_free', serializer.data)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)

    def test_task_serializer_read_only(self):
        """Test TaskSerializer read-only fields"""
        user = User.objects.create_user(
            email='readonly@example.com',
            password='pass123'
        )
        task = Task.objects.create(user=user, description='Test')
        
        from users.serializers.task import TaskSerializer
        serializer = TaskSerializer(task)
        
        # These should be read-only
        self.assertIn('id', serializer.data)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)


class UserModeSettingsSerializerTests(APITestCase):
    """Test user mode settings serializers"""

    def test_settings_serializer_fields(self):
        """Test UserModeSettingsSerializer fields"""
        user = User.objects.create_user(
            email='setserialized@example.com',
            password='pass123'
        )
        settings = UserModeSettings.objects.create(user=user)
        
        from users.serializers.task import UserModeSettingsSerializer
        serializer = UserModeSettingsSerializer(settings)
        
        self.assertIn('ghost_mode_enabled', serializer.data)
        self.assertIn('daily_reminders_enabled', serializer.data)
        self.assertIn('location_sharing_enabled', serializer.data)
        self.assertIn('spotmatch_notifications_enabled', serializer.data)
