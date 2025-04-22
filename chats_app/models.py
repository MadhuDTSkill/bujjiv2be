from collections import defaultdict
from django.db import models
from auth_app.models import User
from helper.models import UUIDPrimaryKey, TimeLine
from .managers import MessageManager
from langchain_core.documents import Document

def str_default_dict():
   return defaultdict(str)

class File(UUIDPrimaryKey, TimeLine):
    file = models.FileField(upload_to='media/files/')
    name = models.CharField(max_length=255)    
    metadata = models.JSONField(null=True, default=str_default_dict)    
    temp_documents = models.JSONField(default=list)   
    
    def add_documents(self, documents : list[Document]):
        documents = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in documents]
        self.temp_documents.extend(documents)
        self.save()
        
    def get_documents(self, metadata : dict = {}):
        documents = []
        for doc in self.temp_documents:
            doc['metadata'].update(metadata)
            documents.append(Document(**doc))
        return documents
    
    def clear_documents(self):
        self.temp_documents = []
        self.save()    

class Conversation(UUIDPrimaryKey, TimeLine):
    title = models.CharField(max_length=255, default="New chat")
    
    endpoint = models.CharField(max_length=255, default="gpt-suite")
    vector_db = models.CharField(max_length=255)
    embedding = models.CharField(max_length=255)
    mode = models.CharField(max_length=255, default="public")
    
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_starred = models.BooleanField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    attachments : list = models.JSONField(default=list, blank=True)  # file_id, file_name, metadata

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    cluster_id = models.CharField(max_length=255, null=True, blank=True)
    
    def add_attachment(self, attachment : dict):
        self.attachments.append(attachment)
        self.save()

    
    class Meta:
        ordering = ['-used_at']

class Message(UUIDPrimaryKey, TimeLine):

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)  

    author = models.JSONField(default=str_default_dict)  # role, name, metadata
    content = models.JSONField(default=str_default_dict)  # content_type, content
    status = models.CharField(max_length=50, default="pending")  # pending, in_progress, completed, failed
    sources = models.JSONField(default=str_default_dict, blank=True)  # retrived_contexts, self_discussion_context
    metadata = models.JSONField(default=str_default_dict, blank=True)  # finish_reason, finished_duration_sec, model_slug, token_usage
    attachments : list = models.JSONField(default=list, blank=True)  # file_id, file_name, metadata
    

    def update_status(self, status, metadata=None):
        self.status = status
        if metadata:
            self.metadata.update(metadata)
        self.save()
        
    def update_self_dicussion_contexts(self, contexts):
        self.sources['self_discussion_context'] += contexts
    
    def update_content(self, content):
        self.content['content'] += content
        
    def update_retrived_contexts(self, context : dict[str:str]):
        self.sources['retrived_contexts'] = context
        
    def add_attachment(self, attachment : dict):
        self.attachments.append(attachment)
        self.save()

    objects : MessageManager = MessageManager()

    class Meta:
        ordering = ['created_at']