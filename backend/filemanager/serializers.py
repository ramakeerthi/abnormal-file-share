from rest_framework import serializers
from .models import File, FileShare

class FileShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileShare
        fields = ('user', 'permission')

class FileSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='uploaded_by.email', read_only=True)
    is_owner = serializers.SerializerMethodField()
    can_download = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    
    class Meta:
        model = File
        fields = ['id', 'name', 'original_name', 'file_size', 'uploaded_at', 
                 'owner_email', 'is_owner', 'can_download', 'can_manage']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.uploaded_by

    def get_can_download(self, obj):
        request = self.context.get('request')
        # Admin can always download
        if request.user.role == 'ADMIN':
            return True
        # Owner can always download
        if request.user == obj.uploaded_by:
            return True
        # Check share permissions for other users
        try:
            share = FileShare.objects.get(file=obj, user=request.user)
            return share.permission == 'DOWNLOAD'
        except FileShare.DoesNotExist:
            return False

    def get_can_manage(self, obj):
        request = self.context.get('request')
        return request.user == obj.uploaded_by or request.user.role == 'ADMIN' 