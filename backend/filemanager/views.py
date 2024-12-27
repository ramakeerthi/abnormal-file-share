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
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Read and encrypt file content
        file_content = file_obj.read()
        encrypted_content = encrypt_file(file_content)

        # Generate file path
        filename = f"{uuid.uuid4()}.encrypted"
        relative_path = f"encrypted_files/{request.user.email}/{filename}"
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        # Create a new file instance
        file_instance = File(
            uploaded_by=request.user,
            original_name=file_obj.name,
            file_size=file_obj.size,
            content_type=file_obj.content_type,
            name=filename,
            file=relative_path
        )

        file_instance.save()

        # Ensure media directory exists
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Create user-specific directory
        user_dir = os.path.join(settings.MEDIA_ROOT, f'encrypted_files/{request.user.email}')
        os.makedirs(user_dir, exist_ok=True)

        with open(full_path, 'wb') as f:
            f.write(encrypted_content)

        serializer = self.get_serializer(file_instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        file_instance = self.get_object()
        # Allow download if user is admin, file owner, or file is shared with them
        if (request.user.role == 'ADMIN' or 
            file_instance.uploaded_by == request.user or 
            request.user in file_instance.shared_with.all()):
            try:
                file_path = os.path.join(settings.MEDIA_ROOT, str(file_instance.file))
                with open(file_path, 'rb') as f:
                    encrypted_content = f.read()
                
                decrypted_content = decrypt_file(encrypted_content)
                
                response = HttpResponse(
                    decrypted_content,
                    content_type=file_instance.content_type
                )
                filename = file_instance.original_name.replace('"', '\\"')
                response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
                response['Access-Control-Expose-Headers'] = 'Content-Disposition'
                response['X-Suggested-Filename'] = filename
                return response
            except Exception as e:
                print(f"Download error: {str(e)}")
                return Response(
                    {'error': 'Failed to download file'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(
            {'error': 'You do not have permission to download this file'},
            status=status.HTTP_403_FORBIDDEN
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