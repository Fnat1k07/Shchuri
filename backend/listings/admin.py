from django.contrib import admin

from .models import Amenity, Listing, ListingImage


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0


@admin.action(description='Схвалити та опублікувати вибрані оголошення')
def approve_listings(modeladmin, request, queryset):
    queryset.update(status=Listing.Status.PUBLISHED)


@admin.action(description='Відхилити та повернути в чернетки')
def reject_listings(modeladmin, request, queryset):
    queryset.update(status=Listing.Status.DRAFT)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'owner',
        'city',
        'price',
        'status',
        'created_at',
    )
    list_filter = ('status', 'property_type', 'city')
    search_fields = ('title', 'address', 'owner__email')
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    inlines = [ListingImageInline]
    actions = [approve_listings, reject_listings]


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('listing', 'is_cover', 'created_at')
    list_filter = ('is_cover', 'created_at')
    search_fields = ('listing__title', 'listing__owner__email')


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
