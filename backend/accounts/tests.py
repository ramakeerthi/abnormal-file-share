from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import User
import pyotp
from unittest.mock import patch

class AuthenticationTests(TestCase):
    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        
        # Test user data for registration
        self.register_data = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'role': 'user'
        }
        
        # Test user data for login
        self.login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }

    def create_test_user(self):
        """Helper method to create a test user"""
        return User.objects.create_user(
            email=self.register_data['email'],
            password=self.register_data['password'],
            role='user'
        )

    def test_user_registration_success(self):
        """Test successful user registration"""
        register_data = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'role': 'USER'
        }
        
        response = self.client.post(
            self.register_url,
            data=register_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=register_data['email']).exists())
        user = User.objects.get(email=register_data['email'])
        self.assertEqual(user.role, register_data['role'])

    def test_user_registration_with_missing_fields(self):
        """Test registration with missing required fields"""
        invalid_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(
            self.register_url,
            invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_with_invalid_email(self):
        """Test registration with invalid email format"""
        invalid_data = self.register_data.copy()
        invalid_data['email'] = 'invalid-email'
        response = self.client.post(
            self.register_url,
            invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_with_password_mismatch(self):
        """Test registration with mismatched passwords"""
        invalid_data = self.register_data.copy()
        invalid_data['password2'] = 'differentpassword'
        response = self.client.post(
            self.register_url,
            invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """Test successful user login with MFA flow"""
        # Create user and set up TOTP
        user = self.create_test_user()
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save()
        
        # First login attempt should return MFA required
        initial_response = self.client.post(
            self.login_url,
            self.login_data,
            format='json'
        )
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)
        self.assertTrue(initial_response.data['mfa_required'])
        self.assertIn('temp_access_token', initial_response.data)
        
        # Complete login with TOTP code
        totp = pyotp.TOTP(secret)
        mfa_login_data = {
            **self.login_data,
            'totp_code': totp.now()
        }
        
        final_response = self.client.post(
            self.login_url,
            mfa_login_data,
            format='json'
        )
        self.assertEqual(final_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', final_response.data)
        self.assertIn('refresh', final_response.data)

    def test_user_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        self.create_test_user()
        invalid_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(
            self.login_url,
            invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_login_with_nonexistent_user(self):
        """Test login with non-existent user"""
        response = self.client.post(
            self.login_url,
            {'email': 'nonexistent@example.com', 'password': 'password123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_logout(self):
        """Test user logout"""
        # Create user and set up TOTP
        user = self.create_test_user()
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save()
        
        # Login with MFA
        totp = pyotp.TOTP(secret)
        login_data = {
            **self.login_data,
            'totp_code': totp.now()
        }
        
        login_response = self.client.post(
            self.login_url,
            login_data,
            format='json'
        )
        
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']
        
        # Set the Authorization header for authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Attempt logout with refresh token in body
        response = self.client.post(
            self.logout_url,
            {'refresh': refresh_token},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_logout_without_token(self):
        """Test logout without authentication token"""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registration_with_existing_email(self):
        """Test registration with an email that already exists"""
        # First create a user
        self.create_test_user()
        
        # Try to register another user with the same email
        response = self.client.post(
            self.register_url,
            self.register_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_totp_setup_flow(self):
        """Test the complete TOTP setup flow"""
        # Register and login a user first
        self.create_test_user()
        login_response = self.client.post(
            self.login_url,
            self.login_data,
            format='json'
        )
        
        # Verify we get MFA setup required response
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertTrue(login_response.data['mfa_setup_required'])
        self.assertIn('temp_access_token', login_response.data)
        
        # Use temporary token for TOTP setup
        temp_token = login_response.data['temp_access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {temp_token}')
        
        # Get TOTP secret and QR code
        totp_setup_url = reverse('mfa-setup')
        setup_response = self.client.get(totp_setup_url)
        self.assertEqual(setup_response.status_code, status.HTTP_200_OK)
        self.assertIn('secret', setup_response.data)
        self.assertIn('qr_code', setup_response.data)
        
        # Verify TOTP setup with valid code
        secret = setup_response.data['secret']
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        
        verify_response = self.client.post(
            totp_setup_url,
            {'totp_code': valid_code},
            format='json'
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

    def test_login_with_mfa(self):
        """Test login process with MFA enabled"""
        # Create user and set up TOTP
        user = self.create_test_user()
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save()
        
        # First login attempt without TOTP code
        initial_response = self.client.post(
            self.login_url,
            self.login_data,
            format='json'
        )
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)
        self.assertTrue(initial_response.data['mfa_required'])
        
        # Second login attempt with valid TOTP code
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        mfa_login_data = {
            **self.login_data,
            'totp_code': valid_code
        }
        
        mfa_response = self.client.post(
            self.login_url,
            mfa_login_data,
            format='json'
        )
        self.assertEqual(mfa_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', mfa_response.data)
        self.assertIn('refresh', mfa_response.data)

    def test_login_with_invalid_mfa_code(self):
        """Test login with invalid MFA code"""
        # Create user and set up TOTP
        user = self.create_test_user()
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save()
        
        # Try login with invalid TOTP code
        invalid_login_data = {
            **self.login_data,
            'totp_code': '000000'
        }
        
        response = self.client.post(
            self.login_url,
            invalid_login_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_totp_setup_with_invalid_code(self):
        """Test TOTP setup with invalid verification code"""
        # Register and login a user first
        self.create_test_user()
        login_response = self.client.post(
            self.login_url,
            self.login_data,
            format='json'
        )
        
        # Use temporary token for TOTP setup
        temp_token = login_response.data['temp_access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {temp_token}')
        
        # Get TOTP secret
        totp_setup_url = reverse('mfa-setup')
        self.client.get(totp_setup_url)
        
        # Try to verify with invalid code
        verify_response = self.client.post(
            totp_setup_url,
            {'totp_code': '000000'},
            format='json'
        )
        self.assertEqual(verify_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', verify_response.data)

    @patch('pyotp.TOTP.verify')
    def test_totp_verification_error_handling(self, mock_verify):
        """Test error handling during TOTP verification"""
        mock_verify.side_effect = Exception("TOTP verification error")
        
        # Create user and set up TOTP
        user = self.create_test_user()
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save()
        
        # First get temporary tokens
        initial_response = self.client.post(
            self.login_url,
            self.login_data,
            format='json'
        )
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)
        self.assertTrue(initial_response.data['mfa_required'])
        
        # Then attempt login with TOTP
        login_data = {
            **self.login_data,
            'totp_code': '123456'
        }
        
        # The view should catch the error and return a 400 response
        response = self.client.post(
            self.login_url,
            login_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
