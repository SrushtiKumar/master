"""
URL configuration for the steganography API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, CryptoKeyViewSet, MediaFileViewSet, CustomAuthToken,
    process_file, download_file, user_stats
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'keys', CryptoKeyViewSet, basename='key')
router.register(r'files', MediaFileViewSet, basename='file')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('auth/register/', UserViewSet.as_view({'post': 'create'}), name='register'),
    path('auth/user/', UserViewSet.as_view({'get': 'me'}), name='current_user'),
    path('user/stats/', user_stats, name='user_stats'),
    path('files/process/', process_file, name='process_file'),
    path('files/<uuid:pk>/download/', download_file, name='download_file'),
]