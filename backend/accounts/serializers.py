from rest_framework import serializers
from .models import User
from django.utils.html import escape

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'role')
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ('role',)  # Make role read-only

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

    def validate_email(self, value):
        return escape(value.strip().lower())

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