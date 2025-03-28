from django.urls import path, include
from .views import LLMResponseListView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('<chat_id>/llm-responses/', LLMResponseListView.as_view(), name='llm-responses'),
]
