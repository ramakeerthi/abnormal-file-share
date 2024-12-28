from django.db import models
from django.conf import settings
import os
import uuid

def user_directory_path(instance, filename):
    return f'encrypted_files/{instance.uploaded_by.email}/{filename}'

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=user_directory_path)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField()
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    client_encryption_key = models.TextField(null=True, blank=True)
    client_encryption_iv = models.TextField(null=True, blank=True)
    is_client_encrypted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.original_name 

    def delete(self, *args, **kwargs):
        if self.file:
            try:
                self.file.delete()
            except Exception as e:
                pass
        super().delete(*args, **kwargs)

class FileShare(models.Model):
    PERMISSION_CHOICES = [
        ('VIEW', 'View Only'),
        ('DOWNLOAD', 'View and Download')
    ]
    
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_files')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='DOWNLOAD')
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('file', 'user') 

class ShareableLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shareable_links')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at'] 