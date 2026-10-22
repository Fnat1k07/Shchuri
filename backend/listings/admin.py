from django.contrib import admin

from .models import Amenity, Listing, ListingImage


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0


@admin.action(description='Опублікувати вибрані')
def make_published(modeladmin, request, queryset):
    queryset.update(status=Listing.Status.PUBLISHED)


@admin.action(description='Повернути в чернетки')
def make_draft(modeladmin, request, queryset):
    queryset.update(status=Listing.Status.DRAFT)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'city', 'price', 'status', 'created_at')
    list_filter = ('status', 'property_type', 'city')
    search_fields = ('title', 'address', 'owner__email')
    inlines = [ListingImageInline]
    actions = [make_published, make_draft]


admin.site.register(Amenity)