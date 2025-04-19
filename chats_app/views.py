from rest_framework.generics import ListAPIView
from .models import LLMResponse
from .serializers import LLMResponseSerializer
from workflow_graphs.bujji.workflow import graph


class LLMResponseListView(ListAPIView):
    
    queryset = LLMResponse.objects.all()
    serializer_class = LLMResponseSerializer
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    
from langchain_core.messages import HumanMessage
    

s = {
        'user_id' : "257f9d6c-6d29-43b3-a014-e22d440d54b3",
        'conversation_id' : "257f9d6c-6d29-43b3-a014-e22d440d54b0",
        "user_query" : "Can you tell me about the history of the world? in 100 words",
        'messages' : [],
        'new_messages' : [],
        'memory_messages' : [],
        'pre_tools' : [],
        'model_name' : 'gemma2-9b-it',
        'response_mode' : 'Scientific',
        'self_discussion' : False,
        '_verbose' : True
    }
    

# for chunk in graph.stream(s):
#     for node, data in chunk.items():
#         print("="*100)
#         print(f"Node: {node}")
#         messages = data.get('messages', [])
#         if len(messages) > 0:
#             print(messages[-1].content)    

