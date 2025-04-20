from rest_framework import serializers
from .models import LLMResponse, Message, Conversation

class LLMResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMResponse
        fields = '__all__'
        
        
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        
class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = str(data['user'])
        return data
        