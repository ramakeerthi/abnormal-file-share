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
                issuer_name="YourAppName"
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
                return Response({'message': 'MFA setup completed successfully'})
            return Response(
                {'error': 'Invalid TOTP code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = (AllowAny,)

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
            temp_tokens = {
                'temp_access_token': str(refresh.access_token),
                'temp_refresh_token': str(refresh)
            }

            # If first login (no TOTP secret set)
            if not user.totp_secret:
                response_data = {
                    'mfa_setup_required': True,
                    **temp_tokens
                }
                return Response(response_data, status=status.HTTP_200_OK)

            # Always require TOTP code for subsequent logins
            if 'totp_code' not in request.data:
                return Response({
                    'mfa_required': True,
                    **temp_tokens
                }, status=status.HTTP_200_OK)

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

            # Generate final tokens after successful MFA
            final_refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(final_refresh),
                'access': str(final_refresh.access_token),
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"message": "Logged out successfully"})
            except TokenError as e:
                return Response(
                    {"error": f"Token Error: {str(e)}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )