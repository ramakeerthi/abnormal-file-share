from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, FileUploadView, FileDownloadView, FileShareView

router = DefaultRouter()
router.register(r'', FileViewSet, basename='file')

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('<uuid:file_id>/download/', FileDownloadView.as_view(), name='file-download'),
    path('<uuid:file_id>/share/', FileShareView.as_view(), name='file-share'),
    path('', include(router.urls)),
] 