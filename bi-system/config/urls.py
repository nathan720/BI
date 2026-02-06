from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # API endpoints
    # path('api/auth/', include('core.auth.urls')),
    # path('api/data/', include('core.dataset.urls')),
    
    # Dashboard / Frontend
    path('', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    # In development, runserver automatically serves static files from app directories.
    # We only need to manually serve media files if any.
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
