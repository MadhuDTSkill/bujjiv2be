from rest_framework import serializers
from .models import Message, Conversation, File


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        exclude = ['documents']
        
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = str(data['user'])
        return data
        
class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = str(data['user'])
        return data
        