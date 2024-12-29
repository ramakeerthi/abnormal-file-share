from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import User
import pyotp
from unittest.mock import patch
from django.conf import settings

class AuthenticationTests(TestCase):
    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()
        # Use reverse() to get the correct URLs
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.mfa_setup_url = reverse('mfa-setup')
        
        # Test user data
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }

    def create_test_user(self, mfa_enabled=False):
        """Helper method to create a test user"""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        if mfa_enabled:
            user.totp_secret = pyotp.random_base32()
            user.save()
        return user

    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(
            self.register_url,
            self.user_data,
            format='json',
            secure=True  # Add this for HTTPS
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

    def test_user_registration_with_missing_fields(self):
        """Test registration with missing fields"""
        invalid_data = {'email': 'test@example.com'}
        response = self.client.post(
            self.register_url,
            invalid_data,
            format='json',
            secure=True
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_with_invalid_email(self):
        """Test registration with invalid email"""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        response = self.client.post(
            self.register_url,
            invalid_data,
            format='json',
            secure=True
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_without_mfa(self):
        """Test login without MFA enabled"""
        user = self.create_test_user()
        
        response = self.client.post(
            self.login_url,
            self.user_data,
            format='json',
            secure=True
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('mfa_setup_required', response.data)

    def test_login_with_mfa(self):
        """Test login with MFA enabled"""
        user = self.create_test_user(mfa_enabled=True)
        totp = pyotp.TOTP(user.totp_secret)
        
        # First login attempt
        response = self.client.post(
            self.login_url,
            self.user_data,
            format='json',
            secure=True
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('mfa_required'))
        
        # Complete login with TOTP
        mfa_data = {
            **self.user_data,
            'totp_code': totp.now()
        }
        
        response = self.client.post(
            self.login_url,
            mfa_data,
            format='json',
            secure=True
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrf_token', response.data)

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        invalid_data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(
            self.login_url,
            invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mfa_setup(self):
        """Test MFA setup process"""
        user = self.create_test_user()
        self.client.force_authenticate(user=user)
        
        # Get TOTP setup data
        response = self.client.get(self.mfa_setup_url, secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('secret', response.data)
        self.assertIn('qr_code', response.data)
        
        # Verify TOTP setup
        totp = pyotp.TOTP(response.data['secret'])
        verify_data = {'totp_code': totp.now()}
        
        response = self.client.post(
            self.mfa_setup_url,
            verify_data,
            format='json',
            secure=True
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
