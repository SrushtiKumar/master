"""
Models for the steganography API.
"""

import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class CryptoKey(models.Model):
    """Model for storing cryptographic keys."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='keys')
    name = models.CharField(max_length=100)
    key_type = models.CharField(max_length=20, choices=[
        ('session', 'Session Key'),
        ('exchange', 'Exchange Key'),
        ('signing', 'Signing Key'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.key_type}) - {self.user.username}"
    
    def key_path(self):
        """Get the path to the key file."""
        return os.path.join(settings.KEY_STORAGE_DIR, f"{self.id}.key")
    
    def public_key_path(self):
        """Get the path to the public key file if applicable."""
        if self.key_type in ['exchange', 'signing']:
            return os.path.join(settings.KEY_STORAGE_DIR, f"{self.id}.pub")
        return None


class MediaFile(models.Model):
    """Model for storing uploaded media files."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=[
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('document', 'Document'),
    ])
    original_file = models.FileField(upload_to='originals/')
    watermarked_file = models.FileField(upload_to='watermarked/', null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    key = models.ForeignKey(CryptoKey, on_delete=models.SET_NULL, null=True, blank=True, related_name='files')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file_name} - {self.user.username}"
