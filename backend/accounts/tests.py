from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import User

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
        """Test successful user login"""
        self.create_test_user()
        response = self.client.post(
            self.login_url,
            self.login_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

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
        # First create and login user
        self.create_test_user()
        login_response = self.client.post(
            self.login_url,
            self.login_data,
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
