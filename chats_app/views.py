import json
from django.http import StreamingHttpResponse
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from .models import LLMResponse
from .serializers import LLMResponseSerializer, ConversationSerializer, MessageSerializer
from workflow_graphs.bujji.workflow import graph
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from . import models
from langchain_core.messages import BaseMessage, AIMessage

class LLMResponseListView(ListAPIView):
    
    queryset = LLMResponse.objects.all()
    serializer_class = LLMResponseSerializer
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    

@method_decorator(csrf_exempt, name='dispatch')
class LLMResponseSSEView(APIView):
    
    def create_human_message(self, conversation_id : str, content_type : str = 'text', content : str | list = '') -> models.Message:
        return models.Message.objects.create_human_message(conversation_id, content_type, content)
        
    def create_assistant_message(self, conversation_id : str, content_type = 'text', content : str | list = '') -> models.Message:
        return models.Message.objects.create_assistant_message(conversation_id, content_type, content= content)
        
        
    def post(self, request, *args, **kwargs):
        user_id = request.user.id
        body = request.data
        with_new_conversation = False


        conversation_id = body.get("conversation_id")
        query = body.get("query", "Hello")
        model_name = body.get("model_name", "gemma2-9b-it")
        response_mode = body.get("response_mode", "Scientific")
        self_discussion_flag = body.get("self_discussion", False)

        if not conversation_id:
            conversation = models.Conversation.objects.create(title="New chat", user_id=user_id)
            conversation_id = conversation.id
            with_new_conversation = True
            
        if not query:
            return StreamingHttpResponse(json.dumps({'error': 'Please provide a query'}), content_type="application/json")
        
        messages : list[models.Message] = [
            self.create_human_message(conversation_id, content=query),
            self.create_assistant_message(conversation_id, content='')
        ]

        s = {
            'user_id': str(user_id),
            'conversation_id': str(conversation_id),
            'user_query': query,
            'messages': [],
            'new_messages': [],
            'memory_messages': [],
            'pre_tools': [],
            'model_name': model_name,
            'response_mode': response_mode,
            'self_discussion': self_discussion_flag,
            '_verbose': True,
        }

        def event_stream():
            self_discussion = False
            tool_calling = False
            
            # yield status that create new conversation with new conversation id
            try:
                if with_new_conversation:
                    p = 'conversation'
                    o = 'add'
                    v = ConversationSerializer(conversation).data
                    yield f"event: new_conversation\ndata: {json.dumps({'p' : p, 'o' : o, 'v' : v})}\n\n"
            
                for message, message_data in graph.stream(s, stream_mode='messages'):
                    message : BaseMessage | AIMessage = message
                    node = message_data.get('langgraph_node')
                    content = message.content or ""
                    response_metadata = message.response_metadata.update(message.usage_metadata) if hasattr(message, 'usage_metadata') and message.usage_metadata else message.response_metadata
                    tool_calls = message.tool_calls if hasattr(message, 'tool_calls') else []
                    tool_call_names = [tool_call['name'] for tool_call in tool_calls]
                    
                    print(f"Tool call names: {tool_call_names}", f"Node: {node}", f"Response metadata: {message.response_metadata}", f"Usage Metadata: {message.usage_metadata if hasattr(message, 'usage_metadata') else {}}")

                    if node == 'init_node':
                        p = 'conversation/message/0'
                        o = "add"
                        v = MessageSerializer(messages[0]).data
                        yield f"event: init_node\ndata: {json.dumps({'p' : p, 'o' : o, 'v' : v})}\n\n"

                    elif node == 'call_self_discussion':
                        if not self_discussion:
                            self_discussion = True
                            p = 'conversation/message/0/sources/self_discussion'
                            o = "add"
                            yield f"event: self_discussion_start\ndata: {json.dumps({'p' : p, 'o' : o})}\n\n"
                        if content:
                            p = 'conversation/message/0/sources/self_discussion'
                            o = "append"
                            v = content
                            messages[1].update_self_dicussion_contexts(content)
                            yield f"event: delta\ndata: {json.dumps({'p' : p, 'o' : o, 'v': v})}\n\n"

                    elif node == 'call_model':
                        if self_discussion:
                            self_discussion = False
                            messages[1].save()
                            yield f"event: self_discussion_end\ndata: {{}}\n\n"
                            
                        if tool_calling:
                            tool_calling = False
                            yield f"event: tool_call_end\ndata: {json.dumps({})}\n\n"
                            
                        if content:
                            p = 'conversation/message/0'
                            o = "append"
                            v = content
                            messages[1].update_content(content)
                            yield f"event: final_response\ndata: {json.dumps({'v': content})}\n\n"
                        
                        if tool_calls:
                            p = 'conversation/message/0/sources/tool_call'
                            o = "add"
                            v = tool_call_names
                            yield f"event: tool_call_start\ndata: {json.dumps({'p' : p, 'o' : o, 'v' : v})}\n\n"
                        
                        if response_metadata:
                            messages[1].update_status('complete', metadata=response_metadata)
                            messages[1].save()
                                               
                    elif node == 'tool_node':
                        tool_calling = True
                        messages[1] = self.create_assistant_message(conversation_id, content='')
                        
                messages[1].update_status('complete', metadata=response_metadata)
                messages[1].save()
                yield f"event: done\ndata: [DONE]\n\n"
            
            except Exception as e:
                print(e)
                # raise e
                messages[1].update_status('error', metadata=response_metadata)
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')