from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, FileUploadView, FileDownloadView

router = DefaultRouter()
router.register(r'', FileViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('download/<uuid:file_id>/', FileDownloadView.as_view(), name='file-download'),
] 