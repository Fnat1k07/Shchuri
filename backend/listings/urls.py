from rest_framework.routers import DefaultRouter

from .views import AmenityViewSet, ListingViewSet, FavoriteViewSet

router = DefaultRouter()
router.register('listings', ListingViewSet, basename='listing')
router.register('amenities', AmenityViewSet, basename='amenity')
router.register('favorites', FavoriteViewSet, basename='favorite')

urlpatterns = router.urls