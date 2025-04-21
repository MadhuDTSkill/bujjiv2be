from django.urls import path, include
from .views import LLMResponseListView, LLMResponseSSEView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('conversation/stream/', LLMResponseSSEView.as_view(), name='conversation_stream'),
]