from rest_framework import serializers
from .models import File
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']

class FileSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.ReadOnlyField(source='uploaded_by.email')
    is_owner = serializers.SerializerMethodField()
    owner_email = serializers.ReadOnlyField(source='uploaded_by.email')
    shared_with = UserSerializer(many=True, read_only=True)
    can_manage = serializers.SerializerMethodField()
    
    class Meta:
        model = File
        fields = ['id', 'name', 'uploaded_by', 'uploaded_at', 'file_size', 
                 'original_name', 'content_type', 'is_owner', 'owner_email', 
                 'shared_with', 'can_manage']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.uploaded_by == request.user or request.user.role == 'ADMIN'
        return False

    def get_can_manage(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.uploaded_by == request.user or request.user.role == 'ADMIN'
        return False

class FileShareSerializer(serializers.Serializer):
    email = serializers.EmailField() 