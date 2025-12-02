from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class CompleteUserAuthTests(APITestCase):
    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.profile_url = '/api/profile/'
        self.logout_url = '/api/auth/logout/'
        self.tokens_url = '/api/auth/tokens/'
        self.tasks_url = '/api/tasks/'
        # user_data as before

        
        self.user_data = {
            'name': 'John Doe',
            'email': 'test@example.com',
            'password': 'testpass123',
            'dateofBirth': '1990-01-01',
            'profile_photo_url': 'https://example.com/avatar.jpg'
        }

    def test_01_register_complete(self):
        """✅ Test registration with avatar_url"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('profile_photo_url', response.data['user'])
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.profile.profile_photo_url, self.user_data['avatar_url'])

    def test_02_login_profile(self):
        """✅ Login → Profile access"""
        self.client.post(self.register_url, self.user_data, format='json')
        login_data = {'email': self.user_data['email'], 'password': self.user_data['password']}
        login_resp = self.client.post(self.login_url, login_data, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_resp.data["token"]}')
        profile_resp = self.client.get(self.profile_url)
        self.assertEqual(profile_resp.status_code, status.HTTP_200_OK)

    def test_03_task_crud(self):
        """✅ Full Task CRUD"""
        self.client.post(self.register_url, self.user_data, format='json')
        login_resp = self.client.post(self.login_url, {
            'email': self.user_data['email'], 'password': self.user_data['password']
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_resp.data["token"]}')
        
        # Create
        task_resp = self.client.post(self.tasks_url, {'description': 'Test Task'}, format='json')
        task_id = task_resp.data['id']
        
        # List & Update
        list_resp = self.client.get(self.tasks_url)
        self.client.put(f'{self.tasks_url}{task_id}/', {'is_transformed_to_quest': True}, format='json')
        self.assertEqual(len(list_resp.data), 1)

    def test_04_logout_revoke(self):
        """✅ Token revocation"""
        self.client.post(self.register_url, self.user_data, format='json')
        login_resp = self.client.post(self.login_url, {
            'email': self.user_data['email'], 'password': self.user_data['password']
        }, format='json')
        token = login_resp.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        self.client.post(self.logout_url)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        fail_resp = self.client.get(self.profile_url)
        self.assertIn(fail_resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])