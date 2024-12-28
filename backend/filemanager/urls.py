from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, FileUploadView, FileDownloadView, FileShareView, ShareableLinkView

router = DefaultRouter()
router.register(r'', FileViewSet, basename='file')

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('download-link/<uuid:link_id>/', ShareableLinkView.as_view(), name='download-shared-link'),
    path('share-link/<uuid:file_id>/', ShareableLinkView.as_view(), name='create-share-link'),
    path('<uuid:file_id>/download/', FileDownloadView.as_view(), name='file-download'),
    path('<uuid:file_id>/share/', FileShareView.as_view(), name='file-share'),
    path('', include(router.urls)),
] 