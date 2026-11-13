from rest_framework import serializers
from django.utils import timezone

from .models import Amenity, Listing, ListingImage, Favorite, ViewingRequest

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


ALLOWED_TRANSITIONS = {
    Listing.Status.DRAFT: {Listing.Status.PENDING, Listing.Status.ARCHIVED},
    Listing.Status.PENDING: {Listing.Status.DRAFT, Listing.Status.ARCHIVED},
    Listing.Status.PUBLISHED: {Listing.Status.ARCHIVED},
    Listing.Status.ARCHIVED: {Listing.Status.DRAFT},
}

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ('id', 'name')

class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ('id', 'image', 'is_cover', 'created_at')
        read_only_fields = ('id', 'is_cover', 'created_at')

    def validate_image(self, value):
        if value.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError(
                f'Файл завеликий. Максимум {MAX_IMAGE_SIZE // (1024 * 1024)} МБ.'
            )
        fmt = getattr(getattr(value, 'image', None), 'format', None)
        if fmt not in ALLOWED_IMAGE_FORMATS:
            raise serializers.ValidationError(
                'Дозволені формати: JPEG, PNG, WEBP.'
            )
        return value

class ListingSerializer(serializers.ModelSerializer):
    amenities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False
    )
    images = ListingImageSerializer(many=True, read_only=True)
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = (
            'id', 'owner', 'title', 'description', 'price', 'property_type',
            'rooms', 'area', 'city', 'district', 'address',
            'latitude', 'longitude', 'amenities', 'images', 'status',
            'is_favorite','views_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'owner', 'views_count', 'created_at', 'updated_at')

    def get_is_favorite(self, obj):
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                return False
    
            favorite_ids = self.context.get('_favorite_ids')
            if favorite_ids is None:
                favorite_ids = set(
                    Favorite.objects.filter(user=request.user)
                    .values_list('listing_id', flat=True)
                )
                self.context['_favorite_ids'] = favorite_ids
            return obj.pk in favorite_ids

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError('Назва має містити щонайменше 5 символів.')
        return value

    def validate_price(self, value):
        if value > 1_000_000:
            raise serializers.ValidationError('Ціна не може перевищувати 1 000 000.')
        return value

    def validate_rooms(self, value):
        if value > 20:
            raise serializers.ValidationError('Кількість кімнат не може перевищувати 20.')
        return value

    def validate_area(self, value):
        if value > 10000:
            raise serializers.ValidationError('Площа не може перевищувати 10 000 м².')
        return value
    
    def validate_status(self, value):
        if self.instance is None:
            if value not in (Listing.Status.DRAFT, Listing.Status.PENDING):
                raise serializers.ValidationError(
                    'Нове оголошення може бути лише draft або pending.'
                )
            return value

        current = self.instance.status
        if value == current:
            return value
        if value not in ALLOWED_TRANSITIONS[current]:
            raise serializers.ValidationError(
                f'Перехід {current} → {value} заборонений.'
            )
        return value

    def validate(self, attrs):
        lat = attrs.get('latitude', getattr(self.instance, 'latitude', None))
        lng = attrs.get('longitude', getattr(self.instance, 'longitude', None))
        if (lat is None) != (lng is None):
            raise serializers.ValidationError(
                'Вкажіть і latitude, і longitude, або жодне з них.'
            )
        return attrs

class ListingDetailSerializer(ListingSerializer):
    contact = serializers.SerializerMethodField()

    class Meta(ListingSerializer.Meta):
        fields = ListingSerializer.Meta.fields + ('contact',)

    def get_contact(self, obj):
        request = self.context.get('request')
        owner = obj.owner
        contact = {
            'name': f'{owner.first_name} {owner.last_name}'.strip(),
            'phone': None,
        }
        if request and request.user.is_authenticated:
            contact['phone'] = owner.phone or None
        return contact

class FavoriteSerializer(serializers.ModelSerializer):
    listing_id = serializers.PrimaryKeyRelatedField(
        source='listing',
        queryset=Listing.objects.filter(status=Listing.Status.PUBLISHED),
        write_only=True,
    )
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'listing', 'listing_id', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        user = self.context['request'].user
        if Favorite.objects.filter(user=user, listing=attrs['listing']).exists():
            raise serializers.ValidationError(
                {'listing_id': ['Це оголошення вже в обраному.']}
            )
        return attrs

class ListingShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ('id', 'title', 'city', 'district', 'address', 'price', 'status')


class ViewingRequestSerializer(serializers.ModelSerializer):
    listing_id = serializers.PrimaryKeyRelatedField(
        source='listing',
        queryset=Listing.objects.filter(status=Listing.Status.PUBLISHED),
        write_only=True,
    )
    listing = ListingShortSerializer(read_only=True)
    tenant = serializers.SerializerMethodField()

    class Meta:
        model = ViewingRequest
        fields = (
            'id', 'listing', 'listing_id', 'tenant', 'preferred_datetime',
            'message', 'status', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'status', 'created_at', 'updated_at')

    def get_tenant(self, obj):
        tenant = obj.tenant
        return {
            'id': tenant.id,
            'name': f'{tenant.first_name} {tenant.last_name}'.strip(),
            'phone': tenant.phone or None,
        }

    def validate_preferred_datetime(self, value):
        if value is not None and value <= timezone.now():
            raise serializers.ValidationError('Дата перегляду має бути в майбутньому.')
        return value

    def validate_message(self, value):
        if len(value) > 1000:
            raise serializers.ValidationError('Повідомлення не може перевищувати 1000 символів.')
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        listing = attrs['listing']
        if listing.owner_id == user.id:
            raise serializers.ValidationError(
                {'listing_id': ['Не можна подати заявку на власне оголошення.']}
            )
        has_pending = ViewingRequest.objects.filter(
            tenant=user, listing=listing, status=ViewingRequest.Status.PENDING
        ).exists()
        if has_pending:
            raise serializers.ValidationError(
                {'listing_id': ['У вас уже є активна заявка на це оголошення.']}
            )
        return attrs