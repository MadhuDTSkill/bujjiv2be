from django.urls import path, include
from .views import LLMResponseSSEView, FileUploadAndProcessView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('files/upload-process/', FileUploadAndProcessView.as_view(), name='file_upload_process'),
    path('conversation/stream/', LLMResponseSSEView.as_view(), name='conversation_stream'),
]