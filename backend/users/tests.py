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