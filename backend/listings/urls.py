from rest_framework.routers import DefaultRouter

from .views import AmenityViewSet, ListingViewSet

router = DefaultRouter()
router.register('listings', ListingViewSet, basename='listing')
router.register('amenities', AmenityViewSet, basename='amenity')

urlpatterns = router.urls