from django.db import models

class MessageManager(models.Manager):
    
    def create_human_message(self, conversation_id : str, content_type : str ='text', content : str | list = ''):
        return self.create(conversation_id=conversation_id, author={'role': 'human', 'name': 'Human'}, content={'content_type': content_type, 'content': content}, status = "complete")
    
    
    def create_assistant_message(self, conversation_id : str, content_type : str ='text', content : str | list = ''):
        return self.create(conversation_id=conversation_id, author={'role': 'assistant', 'name': 'Bujji'}, content={'content_type': content_type, 'content': content})