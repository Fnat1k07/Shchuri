from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    username = None

    email = models.EmailField(
        unique=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    ROLE_CHOICES = (
        ('tenant', 'Орендар'),
        ('owner', 'Власник'),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='tenant'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email