from django.db import models
from auth_app.models import User
from helper.models import UUIDPrimaryKey, TimeLine


class LLMResponse(UUIDPrimaryKey, TimeLine):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='llm_responses')
    prompt = models.TextField()
    response = models.TextField()
    time_taken = models.FloatField(null=True, blank=True)
    tool_responses = models.JSONField(default=list,null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        
    