from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.http import HttpResponse
from .models import File, FileShare, ShareableLink
from .serializers import FileSerializer, FileShareSerializer, ShareableLinkSerializer
from .utils import encrypt_file, decrypt_file
from django.shortcuts import get_object_or_404
import os
import uuid
from django.db import models
from accounts.models import User
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.http import FileResponse
from django.utils.encoding import smart_str
import io
import logging
from django.core.files.storage import default_storage
import time
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_GET

class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve', 'download', 'destroy']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]  # Default to IsAuthenticated for all other actions

    def get_queryset(self):
        user = self.request.user
        action = self.action

        # For the main file list (File Manager screen), show only owned files
        if action == 'list':
            return File.objects.filter(uploaded_by=user)
        
        # For other actions, show files user has access to
        if user.role == 'ADMIN':
            return File.objects.all()
        return File.objects.filter(
            models.Q(uploaded_by=user) | 
            models.Q(shares__user=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            file_obj = request.FILES['file']
            file_data = file_obj.read()
            
            # Encrypt the file data
            encrypted_data = encrypt_file(file_data)
            
            # Create a new in-memory file with encrypted data
            encrypted_file = ContentFile(encrypted_data)
            
            file = File(
                uploaded_by=request.user,
                original_name=file_obj.name,
                file_size=file_obj.size,
                content_type=file_obj.content_type
            )
            
            # Save encrypted file
            file.file.save(f"{uuid.uuid4().hex}.enc", encrypted_file)
            file.save()
            
            return Response({
                'message': 'File uploaded successfully',
                'file_id': file.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Allow access if user is admin, file owner, or file is shared with them
        if (request.user.role == 'ADMIN' or 
            instance.uploaded_by == request.user or 
            request.user in instance.shared_with.all()):
            return super().retrieve(request, *args, **kwargs)
        return Response(
            {'error': 'You do not have permission to access this file'},
            status=status.HTTP_403_FORBIDDEN
        )

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        try:
            file = File.objects.get(id=pk)
            
            # Check if user has access to file
            if not (file.uploaded_by == request.user or request.user in file.shared_with.all()):
                return Response(
                    {"error": "You don't have permission to access this file"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Read encrypted file data
            encrypted_data = file.file.read()
            
            # Get decrypted data
            decrypted_data = decrypt_file(encrypted_data)
            
            # Create response with decrypted content
            response = HttpResponse(
                content=decrypted_data,
                content_type='application/octet-stream'
            )
            
            # Add headers
            response['Content-Disposition'] = f'attachment; filename="{file.original_name}"'
            response['Content-Length'] = len(decrypted_data)
            response['X-Original-Content-Type'] = file.content_type
            
            # Add encryption headers if needed
            if file.is_client_encrypted:
                response['X-Encryption-Key'] = file.client_encryption_key
                response['X-Encryption-IV'] = file.client_encryption_iv
            
            return response
            
        except File.DoesNotExist:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Failed to download file"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            file_path = instance.file.path
            
            # Try to delete file with retries
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    # First try to delete from storage
                    if os.path.exists(file_path):
                        default_storage.delete(instance.file.name)
                    # Then delete the database record
                    instance.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    raise e
                    
        except Exception as e:
            return Response(
                {"error": "Failed to delete file. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        file = self.get_object()
        serializer = FileShareSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user_to_share_with = User.objects.get(email=email)
                
                
                # Don't share if already shared
                if user_to_share_with in file.shared_with.all():
                    return Response(
                        {'error': 'File already shared with this user'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Don't share with file owner
                if user_to_share_with == file.uploaded_by:
                    return Response(
                        {'error': 'Cannot share file with yourself'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                file.shared_with.add(user_to_share_with)
                return Response({'message': 'File shared successfully'})
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def shared(self, request):
        # For admin users, show all files except their own
        if request.user.role == 'ADMIN':
            files = File.objects.exclude(uploaded_by=request.user)
        else:
            # For regular users, show only files shared with them
            files = File.objects.filter(shares__user=request.user)
        
        serializer = self.get_serializer(files, many=True, context={'request': request})
        return Response(serializer.data) 

class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            file_obj = request.FILES['file']
            encryption_key = request.POST.get('encryption_key')
            encryption_iv = request.POST.get('encryption_iv')

            # First read the client-encrypted file
            file_data = file_obj.read()
            
            # Apply server-side encryption
            encrypted_data = encrypt_file(file_data)
            encrypted_file = ContentFile(encrypted_data)
            
            # Create file instance with both client and server encryption info
            file_instance = File.objects.create(
                uploaded_by=request.user,
                original_name=file_obj.name,
                file_size=file_obj.size,
                content_type=file_obj.content_type or 'application/octet-stream',
                client_encryption_key=encryption_key,
                client_encryption_iv=encryption_iv,
                is_client_encrypted=bool(encryption_key and encryption_iv)
            )
            
            # Save the server-encrypted file
            file_instance.file.save(f"{uuid.uuid4().hex}.enc", encrypted_file)
            
            serializer = FileSerializer(file_instance, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SecureFileResponse(HttpResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['Access-Control-Allow-Origin'] = 'https://localhost:3000'
        self['Access-Control-Allow-Credentials'] = 'true'

class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        try:
            file_obj = File.objects.get(id=file_id)
            
            # Check permissions
            has_permission = (
                request.user.role == 'ADMIN' or 
                file_obj.uploaded_by == request.user or 
                FileShare.objects.filter(file=file_obj, user=request.user, permission='DOWNLOAD').exists()
            )
            if not has_permission:
                return Response(
                    {"error": "You don't have permission to download this file"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Read and decrypt server-side encryption
            try:
                with file_obj.file.open('rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = decrypt_file(encrypted_data)
                
            except Exception as e:
                return Response(
                    {"error": f"File read/decrypt failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Create response with server-decrypted data
            try:
                response = HttpResponse(
                    content=decrypted_data,
                    content_type='application/octet-stream'
                )
                
                # Set required headers
                response['Content-Disposition'] = f'attachment; filename="{smart_str(file_obj.original_name)}"'
                response['Content-Length'] = len(decrypted_data)
                response['X-Original-Content-Type'] = file_obj.content_type
                
                if file_obj.is_client_encrypted:
                    if file_obj.client_encryption_key is None or file_obj.client_encryption_iv is None:
                        raise Exception("Client encryption data missing")
                    response['X-Encryption-Key'] = str(file_obj.client_encryption_key)
                    response['X-Encryption-IV'] = str(file_obj.client_encryption_iv)
                
                # Set CORS headers
                response['Access-Control-Allow-Origin'] = 'https://localhost:3000'
                response['Access-Control-Allow-Credentials'] = 'true'
                response['Access-Control-Expose-Headers'] = ', '.join([
                    'Content-Disposition',
                    'Content-Length',
                    'Content-Type',
                    'X-Encryption-Key',
                    'X-Encryption-IV',
                    'X-Original-Content-Type'
                ])
                
                return response
                
            except Exception as e:
                return Response(
                    {"error": f"Failed to create response: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except File.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            return Response(
                {"error": f"Failed to download file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def options(self, request, *args, **kwargs):
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = 'https://localhost:3000'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Accept, Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Expose-Headers'] = ', '.join([
            'Content-Disposition',
            'Content-Length',
            'Content-Type',
            'X-Encryption-Key',
            'X-Encryption-IV',
            'X-Original-Content-Type'
        ])
        return response

class FileShareView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, file_id):
        try:
            file = File.objects.get(id=file_id)
            
            # Check if user is the owner
            if file.uploaded_by != request.user:
                return Response(
                    {"error": "You don't have permission to share this file"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate input
            email = request.data.get('email')
            permission = request.data.get('permission', 'DOWNLOAD')
            
            if not email:
                return Response(
                    {"error": "Email is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if permission not in ['VIEW', 'DOWNLOAD']:
                return Response(
                    {"error": "Invalid permission type"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Don't share with file owner
            if user == file.uploaded_by:
                return Response(
                    {"error": "Cannot share file with yourself"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create or update share
            FileShare.objects.update_or_create(
                file=file,
                user=user,
                defaults={'permission': permission}
            )
            
            return Response({"message": "File shared successfully"})
            
        except File.DoesNotExist:
            return Response(
                {"error": "File not found"}, 
                status=status.HTTP_404_NOT_FOUND
            ) 

class ShareableLinkView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        # Allow unauthenticated access for GET requests (downloading files)
        if self.request.method == 'GET':
            return []
        # Require authentication for POST requests (creating links)
        return [IsAuthenticated()]
    
    def post(self, request, file_id):
        try:
            file = File.objects.get(id=file_id)
            
            # Check if user has permission to share
            if not (request.user == file.uploaded_by or request.user.role == 'ADMIN'):
                return Response(
                    {"error": "You don't have permission to share this file"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate hours
            hours = int(request.data.get('hours', 1))
            if not 1 <= hours <= 24:
                return Response(
                    {"error": "Invalid duration. Must be between 1 and 24 hours"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create shareable link
            expires_at = timezone.now() + timedelta(hours=hours)
            link = ShareableLink.objects.create(
                file=file,
                created_by=request.user,
                expires_at=expires_at
            )
            
            serializer = ShareableLinkSerializer(link, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except File.DoesNotExist:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, link_id):
        try:
            link = get_object_or_404(ShareableLink, id=link_id)
            
            # Check if link has expired
            if link.expires_at < timezone.now():
                return Response(
                    {"error": "This link has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Get the file
            file_obj = link.file
            
            # Read and decrypt server-side encryption
            try:
                with file_obj.file.open('rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = decrypt_file(encrypted_data)
                
            except Exception as e:
                return Response(
                    {"error": f"File read/decrypt failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Create response with server-decrypted data
            try:
                response = HttpResponse(
                    content=decrypted_data,
                    content_type='application/octet-stream'
                )
                
                # Set required headers
                response['Content-Disposition'] = f'attachment; filename="{smart_str(file_obj.original_name)}"'
                response['Content-Length'] = len(decrypted_data)
                response['X-Original-Content-Type'] = file_obj.content_type
                
                if file_obj.is_client_encrypted:
                    response['X-Encryption-Key'] = str(file_obj.client_encryption_key)
                    response['X-Encryption-IV'] = str(file_obj.client_encryption_iv)
                
                # Set CORS headers
                response['Access-Control-Allow-Origin'] = '*'  # Allow any origin for public links
                response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response['Access-Control-Expose-Headers'] = ', '.join([
                    'Content-Disposition',
                    'Content-Length',
                    'Content-Type',
                    'X-Encryption-Key',
                    'X-Encryption-IV',
                    'X-Original-Content-Type'
                ])
                
                return response
                
            except Exception as e:
                return Response(
                    {"error": f"Failed to create response: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            ) 

@require_GET
def favicon_view(request):
    file_path = os.path.join(settings.STATIC_ROOT, 'favicon.ico')
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return HttpResponse(f.read(), content_type="image/x-icon")
    return HttpResponse(status=404) 