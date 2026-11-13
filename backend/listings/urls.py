from rest_framework.routers import DefaultRouter

from .views import AmenityViewSet, ListingViewSet, FavoriteViewSet, ViewingRequestViewSet

router = DefaultRouter()
router.register('listings', ListingViewSet, basename='listing')
router.register('amenities', AmenityViewSet, basename='amenity')
router.register('favorites', FavoriteViewSet, basename='favorite')
router.register('viewing-requests', ViewingRequestViewSet, basename='viewing-request')

urlpatterns = router.urls