from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 🔐 Your single, secure gateway to log into Django's built-in backend database core
    path('admin/', admin.site.urls),
    
    # 🏢 THE ULTIMATE ROOT ROAD: Empty quotes mean your link goes straight to your admin dashboard instantly!
    path('', include('admin_dashboard.urls')),
]

# 🎯 CRITICAL CONTRACT: Connects local development routes to serve media upload paths dynamically
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
