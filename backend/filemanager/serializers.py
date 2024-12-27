from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.ReadOnlyField(source='uploaded_by.email')
    is_owner = serializers.SerializerMethodField()
    
    class Meta:
        model = File
        fields = ['id', 'name', 'uploaded_by', 'uploaded_at', 'file_size', 'original_name', 'content_type', 'is_owner']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.uploaded_by == request.user or request.user.role == 'ADMIN'
        return False 