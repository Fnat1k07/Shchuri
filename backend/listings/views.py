from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import Amenity, Listing, ListingImage
from .permissions import IsOwnerOrReadOnly, IsOwnerRole
from .serializers import (
    AmenitySerializer,
    ListingImageSerializer,
    ListingSerializer,
)

MAX_IMAGES = 8


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [IsOwnerRole, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = Listing.objects.select_related('owner').prefetch_related(
            'amenities', 'images'
        )
        published = Q(status=Listing.Status.PUBLISHED)

        if self.action == 'list':
            return qs.filter(published)

        user = self.request.user
        if user.is_authenticated:
            return qs.filter(published | Q(owner=user))
        return qs.filter(published)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])    
    def mine(self, request):
        qs = (
            Listing.objects.filter(owner=request.user)
            .select_related('owner')
            .prefetch_related('amenities', 'images')
        )

        status_param = request.query_params.get('status')
        if status_param:
            if status_param not in Listing.Status.values:
                allowed = ', '.join(Listing.Status.values)
                return Response(
                    {'status': [f'Допустимі значення: {allowed}.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(status=status_param)

        return Response(self.get_serializer(qs, many=True).data)
    
    @action(detail=True, methods=['post'], url_path='images',
            parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        listing = self.get_object()

        if listing.images.count() >= MAX_IMAGES:
            return Response(
                {'detail': f'Максимум {MAX_IMAGES} фото для одного оголошення.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ListingImageSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        has_cover = listing.images.filter(is_cover=True).exists()
        serializer.save(listing=listing, is_cover=not has_cover)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'images/(?P<image_id>\d+)')
    def delete_image(self, request, pk=None, image_id=None):
        listing = self.get_object()
        image = get_object_or_404(listing.images, pk=image_id)
        was_cover = image.is_cover

        with transaction.atomic():
            image.image.delete(save=False)  # видаляє файл з диска
            image.delete()
            if was_cover:
                next_image = (
                    ListingImage.objects.filter(listing=listing)
                    .order_by('created_at')
                    .first()
                )
                if next_image:
                    next_image.is_cover = True
                    next_image.save(update_fields=['is_cover'])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            url_path=r'images/(?P<image_id>\d+)/cover')
    def set_cover(self, request, pk=None, image_id=None):
        listing = self.get_object()
        image = get_object_or_404(listing.images, pk=image_id)

        with transaction.atomic():
            listing.images.update(is_cover=False)
            image.is_cover = True
            image.save(update_fields=['is_cover'])

        return Response(
            ListingImageSerializer(image, context={'request': request}).data
        )


class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None