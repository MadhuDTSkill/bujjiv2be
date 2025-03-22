from django.urls import path
from .consumers import ChatConsumer

urlpatterns = [
    path('ws/chat', ChatConsumer.as_asgi())
]


