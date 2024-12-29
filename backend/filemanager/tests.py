from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from .models import File, FileShare, ShareableLink
from django.utils import timezone
from datetime import timedelta
from .utils import encrypt_file  # Import the encryption utility
import os
import base64

class FileManagementTests(TestCase):
    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()
        
        # Create test users
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='USER'
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            role='ADMIN'
        )
        
        # Create test file content and encrypt it
        self.test_file_content = b'test file content'
        self.encrypted_content = encrypt_file(self.test_file_content)
        self.test_file = SimpleUploadedFile(
            "test_file.txt",
            self.encrypted_content,
            content_type="text/plain"
        )

    def authenticate_user(self, user):
        """Helper method to authenticate a user"""
        self.client.force_authenticate(user=user)

    def create_test_file(self, user):
        """Helper method to create a test file"""
        return File.objects.create(
            uploaded_by=user,
            file=self.test_file,
            original_name='test1.txt',
            file_size=len(self.test_file_content),
            content_type='text/plain',
            name='test1.txt'  # Add this field
        )

    def test_file_upload(self):
        """Test file upload functionality"""
        self.authenticate_user(self.user)
        
        response = self.client.post(
            reverse('file-upload'),
            {'file': self.test_file},
            format='multipart',
            secure=True
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(File.objects.filter(uploaded_by=self.user).exists())

    def test_file_upload_without_auth(self):
        """Test file upload without authentication"""
        response = self.client.post(
            reverse('file-upload'),
            {'file': self.test_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_file_list(self):
        """Test file listing"""
        self.authenticate_user(self.user)
        
        # Create test file
        self.create_test_file(self.user)
        
        response = self.client.get(reverse('file-list'), secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_file_download(self):
        """Test file download functionality"""
        self.authenticate_user(self.user)
        
        # Create a test file
        file = self.create_test_file(self.user)
        
        response = self.client.get(
            reverse('file-download', kwargs={'file_id': str(file.id)}),
            secure=True
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/octet-stream')

    def test_file_share(self):
        """Test file sharing functionality"""
        self.authenticate_user(self.user)
        
        # Create another user to share with
        share_user = User.objects.create_user(
            email='share@example.com',
            password='sharepass123'
        )
        
        # Create a test file
        file = File.objects.create(
            uploaded_by=self.user,
            file=self.test_file,
            original_name='test1.txt',
            file_size=100,
            content_type='text/plain'
        )
        
        response = self.client.post(
            reverse('file-share', kwargs={'file_id': str(file.id)}),
            {'email': share_user.email, 'permission': 'DOWNLOAD'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            FileShare.objects.filter(
                file=file,
                user=share_user
            ).exists()
        )

    def test_shareable_link_creation(self):
        """Test creation of shareable links"""
        self.authenticate_user(self.user)
        
        # Create a test file
        file = File.objects.create(
            uploaded_by=self.user,
            file=self.test_file,
            original_name='test1.txt',
            file_size=100,
            content_type='text/plain'
        )
        
        response = self.client.post(
            reverse('create-share-link', kwargs={'file_id': str(file.id)}),
            {'hours': 24},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ShareableLink.objects.filter(file=file).exists()
        )

    def test_shared_files_list(self):
        """Test listing of shared files"""
        self.authenticate_user(self.user)
        
        # Create another user and share a file with them
        share_user = User.objects.create_user(
            email='share@example.com',
            password='sharepass123'
        )
        
        file = File.objects.create(
            uploaded_by=self.user,
            file=self.test_file,
            original_name='test1.txt',
            file_size=100,
            content_type='text/plain'
        )
        
        FileShare.objects.create(
            file=file,
            user=share_user,
            permission='DOWNLOAD'
        )
        
        # Switch to shared user
        self.authenticate_user(share_user)
        
        response = self.client.get(reverse('file-shared'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_file_deletion(self):
        """Test file deletion"""
        self.authenticate_user(self.user)
        
        file = File.objects.create(
            uploaded_by=self.user,
            file=self.test_file,
            original_name='test1.txt',
            file_size=100,
            content_type='text/plain'
        )
        
        response = self.client.delete(
            reverse('file-detail', kwargs={'pk': str(file.id)})
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(File.objects.filter(id=file.id).exists())

    def test_shareable_link_access(self):
        """Test accessing file through shareable link"""
        # Create a file and shareable link
        file = self.create_test_file(self.user)
        
        link = ShareableLink.objects.create(
            file=file,
            created_by=self.user,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Try accessing without authentication
        response = self.client.get(
            reverse('download-shared-link', kwargs={'link_id': str(link.id)}),
            secure=True
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expired_shareable_link(self):
        """Test accessing expired shareable link"""
        file = self.create_test_file(self.user)
        
        link = ShareableLink.objects.create(
            file=file,
            created_by=self.user,
            expires_at=timezone.now() - timedelta(hours=1)  # Expired
        )
        
        response = self.client.get(
            reverse('download-shared-link', kwargs={'link_id': str(link.id)}),
            secure=True
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        """Clean up after tests"""
        # Delete test files
        for file in File.objects.all():
            if file.file:
                if os.path.exists(file.file.path):
                    try:
                        os.remove(file.file.path)
                    except OSError:
                        pass
        
        # Clean up media directory if it exists
        media_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media')
        if os.path.exists(media_root):
            for root, dirs, files in os.walk(media_root, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except OSError:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except OSError:
                        pass 