from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from users.views import MeView


schema_view = get_schema_view(
    openapi.Info(
        title="Backend API",
        default_version='v1',
        description="API для React + Django",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        'swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='swagger'
    ),

    path(
        'redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='redoc'
    ),

    path('api/auth/', include('users.urls')),
    path('api/users/me/', MeView.as_view(), name='me'),
    path('api/', include('listings.urls'))
]