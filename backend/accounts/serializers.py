from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('email', 'password', 'role')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        # Use email as username
        validated_data['username'] = validated_data['email']
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class TOTPSetupSerializer(serializers.Serializer):
    totp_code = serializers.CharField(min_length=6, max_length=6)

class TOTPVerifySerializer(serializers.Serializer):
    totp_code = serializers.CharField(min_length=6, max_length=6)

class LoginWithMFASerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    totp_code = serializers.CharField(min_length=6, max_length=6)