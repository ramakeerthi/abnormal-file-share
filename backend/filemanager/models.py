from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import os
import uuid

def user_directory_path(instance, filename):
    # Files will be uploaded to media/encrypted_files/<username>/<filename>
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
    
    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.original_name 