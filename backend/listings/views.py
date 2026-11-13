from django.db import transaction
from django.utils import timezone
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.exceptions import ValidationError, PermissionDenied

from .filters import apply_listing_filters
from .pagination import ListingPagination

from .models import Amenity, Listing, ListingImage, Favorite, ViewingRequest
from .permissions import IsOwnerOrReadOnly, IsOwnerRole, IsTenantRole
from .serializers import (
    AmenitySerializer,
    FavoriteSerializer,
    ListingDetailSerializer,
    ListingImageSerializer,
    ListingSerializer,
    ViewingRequestSerializer,
)

MAX_IMAGES = 8


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [IsOwnerRole, IsOwnerOrReadOnly]
    pagination_class = ListingPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'city', 'district', 'address']
    ordering_fields = ['price', 'created_at', 'area', 'rooms']
    ordering = ['-created_at', '-id']

    def get_queryset(self):
        qs = Listing.objects.select_related('owner').prefetch_related(
            'amenities', 'images'
        )
        published = Q(status=Listing.Status.PUBLISHED)

        if self.action == 'list':
            return apply_listing_filters(qs.filter(published), self.request.query_params)

        user = self.request.user
        if user.is_authenticated:
            return qs.filter(published | Q(owner=user))
        return qs.filter(published)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ListingDetailSerializer
        return ListingSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # рахуємо перегляд лише для опублікованих і не від самого власника
        if (instance.status == Listing.Status.PUBLISHED
                and instance.owner_id != request.user.id):
            Listing.objects.filter(pk=instance.pk).update(
                views_count=F('views_count') + 1
            )
            instance.refresh_from_db(fields=['views_count'])

        return Response(self.get_serializer(instance).data)
    
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

class FavoriteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ListingPagination
    lookup_field = 'listing_id'
    lookup_value_regex = r'\d+'

    def get_queryset(self):
        qs = (
            Favorite.objects.filter(user=self.request.user)
            .select_related('listing__owner')
            .prefetch_related('listing__amenities', 'listing__images')
        )
        if self.action == 'list':
            # оголошення, які зняли з публікації чи заархівували, не показуємо
            qs = qs.filter(listing__status=Listing.Status.PUBLISHED)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ViewingRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ViewingRequestSerializer
    pagination_class = ListingPagination

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsTenantRole()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ViewingRequest.objects.none()

        qs = ViewingRequest.objects.select_related('listing', 'tenant')
        if self.action == 'list':
            qs = qs.filter(tenant=user)
        elif self.action == 'incoming':
            qs = qs.filter(listing__owner=user)
        else:
            qs = qs.filter(Q(tenant=user) | Q(listing__owner=user))

        if self.action in ('list', 'incoming'):
            status_param = self.request.query_params.get('status')
            if status_param:
                if status_param not in ViewingRequest.Status.values:
                    allowed = ', '.join(ViewingRequest.Status.values)
                    raise ValidationError({'status': [f'Допустимі значення: {allowed}.']})
                qs = qs.filter(status=status_param)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)

    @action(detail=False, methods=['get'])
    def incoming(self, request):
        """Заявки на оголошення поточного власника."""
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def _decide(self, request, new_status):
        obj = self.get_object()
        if obj.listing.owner_id != request.user.id:
            raise PermissionDenied('Розглядати заявку може лише власник оголошення.')
        if obj.status != ViewingRequest.Status.PENDING:
            return Response(
                {'detail': 'Заявку вже розглянуто.'}, status=status.HTTP_400_BAD_REQUEST
            )
        if (new_status == ViewingRequest.Status.APPROVED
                and obj.listing.status != Listing.Status.PUBLISHED):
            return Response(
                {'detail': 'Оголошення не опубліковане.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # умовне оновлення захищає від подвійного розгляду при одночасних запитах
        updated = ViewingRequest.objects.filter(
            pk=obj.pk, status=ViewingRequest.Status.PENDING
        ).update(status=new_status, updated_at=timezone.now())
        if not updated:
            return Response(
                {'detail': 'Заявку вже розглянуто.'}, status=status.HTTP_400_BAD_REQUEST
            )
        obj.refresh_from_db()
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return self._decide(request, ViewingRequest.Status.APPROVED)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self._decide(request, ViewingRequest.Status.REJECTED)

    def destroy(self, request, *args, **kwargs):
        """Орендар скасовує власну заявку, поки її не розглянули."""
        obj = self.get_object()
        if obj.tenant_id != request.user.id:
            raise PermissionDenied('Скасувати заявку може лише її автор.')
        if obj.status != ViewingRequest.Status.PENDING:
            return Response(
                {'detail': 'Розглянуту заявку скасувати не можна.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)