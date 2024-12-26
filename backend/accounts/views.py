from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserRegistrationSerializer, UserLoginSerializer, TOTPSetupSerializer, TOTPVerifySerializer, LoginWithMFASerializer
from rest_framework_simplejwt.exceptions import TokenError
import pyotp
import qrcode
import io
import base64
from django.conf import settings
from django.middleware.csrf import get_token
from django.http import JsonResponse
from .authentication import CookieJWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView
from .models import User
from rest_framework.exceptions import PermissionDenied

class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TOTPSetupView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CookieJWTAuthentication,)

    def get(self, request):
        try:
            # Generate new TOTP secret
            secret = pyotp.random_base32()
            request.user.totp_secret = secret
            request.user.save()

            # Generate QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                request.user.email,
                issuer_name="secure-file-share"
            )

            # Create QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

            return Response({
                'secret': secret,
                'qr_code': qr_code_base64
            })
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def post(self, request):
        serializer = TOTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            totp = pyotp.TOTP(request.user.totp_secret)
            if totp.verify(serializer.validated_data['totp_code']):
                response = Response({'message': 'MFA setup completed successfully'})
                # Clear temporary token cookie
                response.delete_cookie('temp_token')
                return response
            return Response(
                {'error': 'Invalid TOTP code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = []

    def post(self, request):
        if 'totp_code' in request.data:
            serializer = LoginWithMFASerializer(data=request.data)
        else:
            serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = authenticate(
                request,
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            if not user:
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Generate temporary token for both MFA setup and verification
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'user': {
                    'email': user.email,
                    'role': user.role,
                },
                'csrf_token': get_token(request)
            }

            if not user.totp_secret:
                response_data['mfa_setup_required'] = True
                response = Response(response_data)
                # Set temporary token as HTTP-only cookie
                response.set_cookie(
                    'temp_token',
                    str(refresh.access_token),
                    httponly=True,
                    samesite='Strict',
                    secure=not settings.DEBUG
                )
                return response

            if 'totp_code' not in request.data:
                response_data['mfa_required'] = True
                response = Response(response_data)
                response.set_cookie(
                    'temp_token',
                    str(refresh.access_token),
                    httponly=True,
                    samesite='Strict',
                    secure=not settings.DEBUG
                )
                return response

            try:
                totp = pyotp.TOTP(user.totp_secret)
                if not totp.verify(serializer.validated_data['totp_code']):
                    return Response(
                        {'error': 'Invalid TOTP code'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Set HTTP-only cookies for JWT tokens
            response = Response(response_data)
            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE'],
                str(refresh.access_token),
                httponly=True,
                samesite='Strict',
                secure=not settings.DEBUG
            )
            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                str(refresh),
                httponly=True,
                samesite='Strict',
                secure=not settings.DEBUG
            )
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CookieJWTAuthentication,)

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            response = Response({"message": "Logged out successfully"})
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            response.delete_cookie('temp_token')
            return response
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class CheckAuthView(APIView):
    permission_classes = (AllowAny,)
    
    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'authenticated': True,
                'user': {
                    'email': request.user.email,
                    'role': request.user.role,
                }
            })
        return Response({
            'authenticated': False,
            'user': None
        }, status=status.HTTP_200_OK)  # Return 200 even when not authenticated

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token:
            request.data['refresh'] = refresh_token
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE'],
                response.data['access'],
                httponly=True,
                samesite='Strict',
                secure=not settings.DEBUG
            )
            del response.data['access']
        
        return response

class UserManagementView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CookieJWTAuthentication,)

    def get(self, request):
        if request.user.role != 'ADMIN':
            raise PermissionDenied("Only admins can access user management")
        
        try:            
            # Get all users first
            all_users = User.objects.all()
            # Then exclude current user
            users = all_users.exclude(id=request.user.id)
            
            user_data = [{
                'id': user.id,
                'email': user.email,
                'role': user.role
            } for user in users]
            return Response(user_data)
            
        except Exception as e:
            print(f"Error in UserManagementView: {str(e)}")  # Add this for debugging
            return Response(
                {"error": "Failed to fetch users"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            raise PermissionDenied("Only admins can update user roles")
        
        user_id = request.data.get('id')
        new_role = request.data.get('role')
        
        if not user_id or not new_role:
            return Response(
                {"error": "User ID and role are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            if user == request.user:
                return Response(
                    {"error": "Cannot modify your own role"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.role = new_role
            user.save()
            return Response({
                'id': user.id,
                'email': user.email,
                'role': user.role
            })
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )