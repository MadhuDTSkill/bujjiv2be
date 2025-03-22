from rest_framework import serializers
from .models import LLMResponse

class LLMResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMResponse
        fields = '__all__'
        