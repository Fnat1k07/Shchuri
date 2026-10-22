from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Listing
from .permissions import IsOwnerOrReadOnly, IsOwnerRole
from .serializers import ListingSerializer


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [IsOwnerRole, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = Listing.objects.select_related('owner').prefetch_related('amenities')
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
            .prefetch_related('amenities')
        )
        return Response(self.get_serializer(qs, many=True).data)