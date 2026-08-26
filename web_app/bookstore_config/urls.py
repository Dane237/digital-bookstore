from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Clean, native Django admin path
    path('admin/', admin.site.urls),

    # 2. Your custom dashboard path
    path('dashboard/', include('admin_dashboard.urls')),
]

# 🎯 CRITICAL CONTRACT: Connects local development routes to serve media upload paths dynamically
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
