"""
Views for the steganography API.
"""

import os
import sys
import tempfile
from django.conf import settings
from django.http import FileResponse
from django.db.models import Count
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.parsers import MultiPartParser, FormParser

# Add the parent directory to sys.path to import stegano_toolkit
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stegano_toolkit.common_crypto import KeyManager, PayloadProcessor
from stegano_toolkit.image_stego import ImageSteganography
from stegano_toolkit.audio_stego import AudioSteganography
from stegano_toolkit.video_stego import VideoSteganography
from stegano_toolkit.document_stego import DocumentSteganography

from .models import CryptoKey, MediaFile
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    CryptoKeySerializer, MediaFileSerializer
)
from django.contrib.auth.models import User

# User statistics endpoint
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get statistics for the current user."""
    user = request.user
    file_count = MediaFile.objects.filter(user=user).count()
    key_count = CryptoKey.objects.filter(user=user).count()
    
    return Response({
        'file_count': file_count,
        'key_count': key_count,
        'username': user.username,
        'email': user.email,
        'date_joined': user.date_joined
    })

# File processing endpoint
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def process_file(request):
    """Process a file with steganography (embed or extract)."""
    operation = request.data.get('operation')
    file = request.FILES.get('file')
    key_id = request.data.get('key_id')
    message = request.data.get('message', '')
    
    if not file:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    if not key_id:
        return Response({"error": "No key provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        key_obj = CryptoKey.objects.get(id=key_id, user=request.user)
    except CryptoKey.DoesNotExist:
        return Response({"error": "Key not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Determine file type
    filename = file.name.lower()
    if filename.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
        file_type = 'image'
    elif filename.endswith(('.mp3', '.wav', '.ogg')):
        file_type = 'audio'
    elif filename.endswith(('.mp4', '.avi', '.mov')):
        file_type = 'video'
    elif filename.endswith(('.pdf', '.docx')):
        file_type = 'document'
    else:
        return Response({"error": "Unsupported file type"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create a new media file record
    media_file = MediaFile.objects.create(
        user=request.user,
        name=file.name,
        file_type=file_type,
        original_file=file
    )
    
    # Process the file based on operation
    try:
        with open(key_obj.key_path(), 'rb') as f:
            key = f.read()
        
        handler = get_steganography_handler(file_type)
        
        if operation == 'embed':
            if not message:
                return Response({"error": "No message provided for embedding"}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Process the payload
            payload, _ = PayloadProcessor.prepare_payload(message.encode('utf-8'), key)
            
            # Create a temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Embed the payload
            output_path = os.path.join(settings.MEDIA_ROOT, f"processed_{media_file.id}.{filename.split('.')[-1]}")
            handler.embed(temp_file_path, output_path, payload)
            
            # Save the processed file
            media_file.processed_file = f"processed_{media_file.id}.{filename.split('.')[-1]}"
            media_file.save()
            
            # Clean up
            os.unlink(temp_file_path)
            
            return Response({
                "id": media_file.id,
                "message": "File processed successfully",
                "file_url": media_file.processed_file.url if media_file.processed_file else None
            })
        
        elif operation == 'extract':
            # Create a temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Extract the payload
            extracted_payload = handler.extract(temp_file_path)
            
            # Decrypt the payload
            decrypted_message = PayloadProcessor.process_payload(extracted_payload, key)
            
            # Clean up
            os.unlink(temp_file_path)
            
            return Response({
                "id": media_file.id,
                "message": decrypted_message.decode('utf-8')
            })
        
        else:
            return Response({"error": "Invalid operation"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Helper function to get steganography handler
def get_steganography_handler(file_type):
    """Get the appropriate steganography handler for the file type."""
    if file_type == 'image':
        return ImageSteganography()
    elif file_type == 'audio':
        return AudioSteganography()
    elif file_type == 'video':
        return VideoSteganography()
    elif file_type in ['document', 'pdf', 'docx']:
        return DocumentSteganography()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

# File download endpoint
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_file(request, pk):
    """Download a processed file."""
    try:
        media_file = MediaFile.objects.get(id=pk, user=request.user)
    except MediaFile.DoesNotExist:
        return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if not media_file.processed_file:
        return Response({"error": "No processed file available"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        response = FileResponse(media_file.processed_file.open('rb'), 
                               as_attachment=True, 
                               filename=f"processed_{media_file.name}")
        return response
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomAuthToken(ObtainAuthToken):
    """Custom auth token view that returns user info with token."""
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email
        })


class UserViewSet(viewsets.ModelViewSet):
    """API endpoint for user registration and management."""
    queryset = Token.objects.none()  # Required for DRF
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    def create(self, request):
        """Register a new user."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's information."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class CryptoKeyViewSet(viewsets.ModelViewSet):
    """API endpoint for cryptographic key management."""
    serializer_class = CryptoKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CryptoKey.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        key_type = serializer.validated_data.get('key_type')
        key_instance = serializer.save(user=self.request.user)
        
        # Generate and save the actual key
        if key_type == 'session':
            key = KeyManager.generate_session_key()
            with open(key_instance.key_path(), 'wb') as f:
                f.write(key)
        elif key_type in ['exchange', 'signing']:
            if key_type == 'exchange':
                private_key, public_key = KeyManager.generate_keypair()
            else:  # signing
                private_key, public_key = KeyManager.generate_signing_keypair()
                
            with open(key_instance.key_path(), 'wb') as f:
                f.write(private_key)
            with open(key_instance.public_key_path(), 'wb') as f:
                f.write(public_key)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the key file."""
        key = self.get_object()
        try:
            with open(key.key_path(), 'rb') as f:
                response = FileResponse(f, as_attachment=True, filename=f"{key.name}.key")
                return response
        except FileNotFoundError:
            return Response({"error": "Key file not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def download_public(self, request, pk=None):
        """Download the public key file if applicable."""
        key = self.get_object()
        if key.key_type not in ['exchange', 'signing']:
            return Response({"error": "No public key available for this key type"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with open(key.public_key_path(), 'rb') as f:
                response = FileResponse(f, as_attachment=True, filename=f"{key.name}.pub")
                return response
        except FileNotFoundError:
            return Response({"error": "Public key file not found"}, status=status.HTTP_404_NOT_FOUND)


class MediaFileViewSet(viewsets.ModelViewSet):
    """API endpoint for media file management and steganography operations."""
    serializer_class = MediaFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return MediaFile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_steganography_handler(self, file_type):
        """Get the appropriate steganography handler for the file type."""
        if file_type == 'image':
            return ImageSteganography()
        elif file_type == 'audio':
            return AudioSteganography()
        elif file_type == 'video':
            return VideoSteganography()
        elif file_type in ['document', 'pdf', 'docx']:
            return DocumentSteganography()
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    @action(detail=True, methods=['post'])
    def embed(self, request, pk=None):
        """Embed a message in the media file using steganography."""
        media_file = self.get_object()
        
        # Check if we have all required data
        if not media_file.original_file:
            return Response({"error": "No original file uploaded"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        message = request.data.get('message')
        if not message:
            return Response({"error": "No message provided"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        key_id = request.data.get('key_id')
        if not key_id:
            return Response({"error": "No key provided"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            key_obj = CryptoKey.objects.get(id=key_id, user=request.user)
        except CryptoKey.DoesNotExist:
            return Response({"error": "Key not found"}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Read the key
            with open(key_obj.key_path(), 'rb') as f:
                key = f.read()
            
            # Read the original file
            with media_file.original_file.open('rb') as f:
                original_data = f.read()
            
            # Process the payload
            payload, _ = PayloadProcessor.prepare_payload(message.encode('utf-8'), key)
            
            # Get the appropriate handler
            handler = self.get_steganography_handler(media_file.file_type)
            
            # Embed the payload
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                output_data = handler.embed(original_data, payload, key)
                temp_file.write(output_data)
                temp_file_path = temp_file.name
            
            # Save the watermarked file
            filename = os.path.basename(media_file.original_file.name)
            with open(temp_file_path, 'rb') as f:
                media_file.watermarked_file.save(f"watermarked_{filename}", f)
            
            # Clean up
            os.unlink(temp_file_path)
            
            # Update the media file record
            media_file.message = message
            media_file.key = key_obj
            media_file.save()
            
            return Response({
                "success": True,
                "media_file": MediaFileSerializer(media_file).data
            })
            
        except Exception as e:
            return Response({"error": str(e)}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def extract(self, request, pk=None):
        """Extract a message from the media file using steganography."""
        media_file = self.get_object()
        
        # Check if we have all required data
        if not media_file.watermarked_file:
            return Response({"error": "No watermarked file available"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        if not media_file.key:
            return Response({"error": "No key associated with this file"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Read the key
            with open(media_file.key.key_path(), 'rb') as f:
                key = f.read()
            
            # Read the watermarked file
            with media_file.watermarked_file.open('rb') as f:
                watermarked_data = f.read()
            
            # Get the appropriate handler
            handler = self.get_steganography_handler(media_file.file_type)
            
            # Extract the payload
            payload = handler.extract(watermarked_data, key)
            
            # Process the payload
            message = PayloadProcessor.extract_payload(payload, key)
            
            return Response({
                "success": True,
                "message": message.decode('utf-8')
            })
            
        except Exception as e:
            return Response({"error": str(e)}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download_original(self, request, pk=None):
        """Download the original file."""
        media_file = self.get_object()
        if not media_file.original_file:
            return Response({"error": "No original file available"}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        return FileResponse(media_file.original_file, as_attachment=True, 
                           filename=media_file.file_name)
    
    @action(detail=True, methods=['get'])
    def download_watermarked(self, request, pk=None):
        """Download the watermarked file."""
        media_file = self.get_object()
        if not media_file.watermarked_file:
            return Response({"error": "No watermarked file available"}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        return FileResponse(media_file.watermarked_file, as_attachment=True, 
                           filename=f"watermarked_{media_file.file_name}")
