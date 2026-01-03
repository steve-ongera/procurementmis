from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import your custom error views from your app (pms)
from pms import views as pms_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include your app URLs
    path('', include('pms.urls')),  # Your app urls.py
]

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = pms_views.custom_404
handler500 = pms_views.custom_500
