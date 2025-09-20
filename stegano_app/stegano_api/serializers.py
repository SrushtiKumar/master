"""
Serializers for the steganography API.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CryptoKey, MediaFile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class CryptoKeySerializer(serializers.ModelSerializer):
    """Serializer for CryptoKey model."""
    
    class Meta:
        model = CryptoKey
        fields = ['id', 'name', 'key_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class MediaFileSerializer(serializers.ModelSerializer):
    """Serializer for MediaFile model."""
    key = CryptoKeySerializer(read_only=True)
    key_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = MediaFile
        fields = ['id', 'file_name', 'file_type', 'original_file', 
                  'watermarked_file', 'message', 'key', 'key_id', 'created_at']
        read_only_fields = ['id', 'watermarked_file', 'created_at']
    
    def create(self, validated_data):
        key_id = validated_data.pop('key_id', None)
        user = self.context['request'].user
        
        media_file = MediaFile.objects.create(
            user=user,
            **validated_data
        )
        
        if key_id:
            try:
                key = CryptoKey.objects.get(id=key_id, user=user)
                media_file.key = key
                media_file.save()
            except CryptoKey.DoesNotExist:
                pass
        
        return media_file