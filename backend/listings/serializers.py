from rest_framework import serializers

from .models import Amenity, Listing, ListingImage

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

    class Meta:
        model = Listing
        fields = (
            'id', 'owner', 'title', 'description', 'price', 'property_type',
            'rooms', 'area', 'city', 'district', 'address',
            'latitude', 'longitude', 'amenities', 'images', 'status',
            'views_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'owner', 'views_count', 'created_at', 'updated_at')

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