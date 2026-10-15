from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        'email',
        'first_name',
        'last_name',
        'phone',
        'role',
        'is_staff', 
    )

    ordering = ('email',)

    fieldsets = (
        (None, {
            'fields': (
                'email',
                'password',
            )
        }),
        ('Особиста інформація', {
            'fields': (
                'first_name',
                'last_name',
                'phone',
                'role',
            )
        }),
        ('Права доступу', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'phone',
                'role',
            ),
        }),
    )

    search_fields = (
        'email',
        'first_name',
        'last_name',
    )