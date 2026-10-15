from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class RegisterTests(APITestCase):
    def setUp(self):
        self.url = reverse('register')
        self.data = {
            'email': 'owner@example.com',
            'first_name': 'Іван',
            'last_name': 'Петренко',
            'phone': '+380501234567',
            'role': 'owner',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }

    def test_register_success(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='owner@example.com').exists())
        self.assertNotIn('password', response.data)

    def test_duplicate_email_case_insensitive(self):
        self.client.post(self.url, self.data, format='json')
        self.data['email'] = 'Owner@Example.com'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_passwords_do_not_match(self):
        self.data['password2'] = 'Other123!'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password(self):
        self.data['password'] = self.data['password2'] = '12345678'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_role(self):
        self.data['role'] = 'admin'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_become_staff(self):
        self.data['is_staff'] = True
        self.client.post(self.url, self.data, format='json')
        user = User.objects.get(email='owner@example.com')
        self.assertFalse(user.is_staff)

class LoginTests(APITestCase):
    def setUp(self):
        self.login_url = reverse('login')
        self.refresh_url = reverse('token_refresh')
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
            first_name='Іван',
            last_name='Петренко',
            role='tenant',
        )

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {'email': 'user@example.com', 'password': 'StrongPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'user@example.com')
        self.assertEqual(response.data['user']['role'], 'tenant')

    def test_login_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {'email': 'user@example.com', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_email(self):
        response = self.client.post(
            self.login_url,
            {'email': 'nobody@example.com', 'password': 'StrongPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        login = self.client.post(
            self.login_url,
            {'email': 'user@example.com', 'password': 'StrongPass123!'},
            format='json',
        )
        response = self.client.post(
            self.refresh_url,
            {'refresh': login.data['refresh']},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_invalid_token(self):
        response = self.client.post(
            self.refresh_url, {'refresh': 'not-a-token'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class ProfileTests(APITestCase):
    def setUp(self):
        self.url = reverse('me')
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
            first_name='Іван',
            last_name='Петренко',
            role='tenant',
        )

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user@example.com')
        self.assertNotIn('password', response.data)

    def test_patch_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            self.url, {'first_name': 'Петро', 'phone': '+380501234567'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Петро')
        self.assertEqual(self.user.phone, '+380501234567')

    def test_cannot_change_role_or_email(self):
        self.client.force_authenticate(self.user)
        self.client.patch(
            self.url, {'role': 'owner', 'email': 'new@example.com'}, format='json'
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'tenant')
        self.assertEqual(self.user.email, 'user@example.com')

    def test_put_not_allowed(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)