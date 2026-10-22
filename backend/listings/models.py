from django.db import models
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'amenities'
        ordering = ['name']

    def __str__(self):
        return self.name

class Listing(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Чернетка'
        PENDING = 'pending', 'На модерації'
        PUBLISHED = 'published', 'Опубліковано'
        ARCHIVED = 'archived', 'В архіві'

    class PropertyType(models.TextChoices):
        APARTMENT = 'apartment', 'Квартира'
        HOUSE = 'house', 'Будинок'
        ROOM = 'room', 'Кімната'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Ціна за місяць',
    )
    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, default=PropertyType.APARTMENT
    )
    rooms = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    area = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('1'))],
        help_text='Площа, м²',
    )

    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    amenities = models.ManyToManyField(Amenity, blank=True, related_name='listings')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='images'
    )
    image = models.ImageField(upload_to='listings/')
    is_cover = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_cover', 'created_at']

    def __str__(self):
        return f'Фото {self.pk} для {self.listing_id}'

# Create your models here.
