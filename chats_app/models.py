from collections import defaultdict
from django.db import models
from auth_app.models import User
from helper.models import UUIDPrimaryKey, TimeLine
from .managers import MessageManager

def str_default_dict():
   return defaultdict(str)


class LLMResponse(UUIDPrimaryKey, TimeLine):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='llm_responses')
    prompt = models.TextField()
    response = models.TextField()
    time_taken = models.FloatField(null=True, blank=True)
    tool_responses = models.JSONField(default=list,null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        
        
class File(UUIDPrimaryKey, TimeLine):
    file = models.FileField(upload_to='files/')
    name = models.CharField(max_length=255)    
    metadata = models.JSONField(null=True, default=str_default_dict)        

class Conversation(UUIDPrimaryKey, TimeLine):

    title = models.CharField(max_length=255, default="New chat")

    is_archived = models.BooleanField(default=False)
    is_starred = models.BooleanField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    files = models.ManyToManyField(File, related_name='conversations')
    
    class Meta:
        ordering = ['-used_at']

class Message(UUIDPrimaryKey, TimeLine):

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)  

    author = models.JSONField(default=str_default_dict)  # role, name, metadata
    content = models.JSONField(default=str_default_dict)  # content_type, content
    status = models.CharField(max_length=50, default="pending")  # pending, in_progress, completed, failed
    sources = models.JSONField(default=str_default_dict, blank=True)  # retrived_contexts, self_discussion_context, tool_responses
    metadata = models.JSONField(default=str_default_dict, blank=True)  # finish_reason, finished_duration_sec, model_slug, token_usage

    def update_status(self, status, metadata=None):
        self.status = status
        if metadata:
            self.metadata.update(metadata)
        self.save()
        
    def update_self_dicussion_contexts(self, contexts):
        self.sources['self_discussion_context'] += contexts
    
    def update_content(self, content):
        self.content['content'] += content

    objects : MessageManager = MessageManager()

    class Meta:
        ordering = ['created_at']