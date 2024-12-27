from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.http import HttpResponse
from .models import File
from .serializers import FileSerializer, FileShareSerializer
from .utils import encrypt_file, decrypt_file
import os
import uuid
from django.db import models
from accounts.models import User
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView

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
        
        # For other actions (like download, share, etc.), admins can access all files
        # and regular users can access their own files and shared files
        if user.role == 'ADMIN':
            return File.objects.all()
        return File.objects.filter(
            models.Q(uploaded_by=user) | 
            models.Q(shared_with=user)
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
            
            # Get encryption parameters for client-side decryption
            decryption_data = decrypt_file(encrypted_data)
            
            return Response({
                'filename': file.original_name,
                'content_type': file.content_type,
                'salt': decryption_data['salt'],
                'iv': decryption_data['iv'],
                'content': decryption_data['content']
            })
            
        except File.DoesNotExist:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role != 'ADMIN' and instance.uploaded_by != request.user:
            return Response(
                {'error': 'You do not have permission to delete this file'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Delete the physical file
            file_path = os.path.join(settings.MEDIA_ROOT, str(instance.file))
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete the database record
            instance.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(f"Delete error: {str(e)}")
            return Response(
                {'error': 'Failed to delete file'},
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
                
                # Add debug logging
                print(f"File owner: {file.uploaded_by.email}")
                print(f"User to share with: {user_to_share_with.email}")
                print(f"Are they the same? {file.uploaded_by == user_to_share_with}")
                
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
            files = File.objects.filter(shared_with=request.user)
        
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data) 

class FileUploadView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
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

class FileDownloadView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, file_id):
        try:
            file = File.objects.get(id=file_id)
            
            # Check if user has access to file
            if not (file.uploaded_by == request.user or request.user in file.shared_with.all()):
                return Response(
                    {"error": "You don't have permission to access this file"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check if file exists on disk
            if not file.file or not os.path.exists(file.file.path):
                # Remove sharing relationships if file doesn't exist
                file.shared_with.clear()
                file.delete()
                return Response(
                    {"error": "File no longer exists"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Read encrypted file data
            try:
                with file.file.open('rb') as f:
                    encrypted_data = f.read()
            except IOError:
                # Handle case where file can't be read
                file.shared_with.clear()
                file.delete()
                return Response(
                    {"error": "File is corrupted or unavailable"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get encryption parameters for client-side decryption
            try:
                decryption_data = decrypt_file(encrypted_data)
                return Response({
                    'filename': file.original_name,
                    'content_type': file.content_type,
                    'salt': decryption_data['salt'],
                    'iv': decryption_data['iv'],
                    'content': decryption_data['content']
                })
            except Exception as e:
                print(f"Decryption error: {str(e)}")
                return Response(
                    {"error": "Failed to process file"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except File.DoesNotExist:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND
            ) 