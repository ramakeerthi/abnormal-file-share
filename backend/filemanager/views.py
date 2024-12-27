from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.http import HttpResponse
from .models import File
from .serializers import FileSerializer
from .utils import encrypt_file, decrypt_file
import os
import uuid

class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve', 'download', 'destroy']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]  # Default to IsAuthenticated for all other actions

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return File.objects.all()
        return File.objects.filter(uploaded_by=user)

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
        # Ensure users can only access their own files (except admins)
        instance = self.get_object()
        if request.user.role != 'ADMIN' and instance.uploaded_by != request.user:
            return Response(
                {'error': 'You do not have permission to access this file'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        # Get the file instance and check permissions
        file_instance = self.get_object()
        if request.user.role != 'ADMIN' and file_instance.uploaded_by != request.user:
            return Response(
                {'error': 'You do not have permission to download this file'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            file_path = os.path.join(settings.MEDIA_ROOT, str(file_instance.file))
            with open(file_path, 'rb') as f:
                encrypted_content = f.read()
            
            decrypted_content = decrypt_file(encrypted_content)
            
            response = HttpResponse(
                decrypted_content,
                content_type=file_instance.content_type
            )
            # Properly format the Content-Disposition header
            filename = file_instance.original_name.replace('"', '\\"')  # Escape quotes
            response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
            # Add additional headers for better browser compatibility
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            response['X-Suggested-Filename'] = filename
            return response
        except Exception as e:
            print(f"Download error: {str(e)}")  # Add logging for debugging
            return Response(
                {'error': 'Failed to download file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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