"""
stegano_web URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache

# Serve the React app with a never_cache decorator to prevent caching issues
index_view = never_cache(TemplateView.as_view(template_name='index.html'))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('stegano_api.urls')),
    path('', index_view, name='frontend'),
]

# Always serve media files in both debug and production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
