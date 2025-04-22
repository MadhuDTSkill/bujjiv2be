import os
import json
import tempfile
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ConversationSerializer, MessageSerializer, FileSerializer
from workflow_graphs.bujji.workflow import graph
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from . import models
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.documents import Document
from workflow_graphs.bujji.loaders import DynamicLoader
from workflow_graphs.bujji.vector_dbs import PineconeVectorDB

class FileUploadAndProcessView(APIView):    
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        
        def event_stream():
            total_steps = 5

            if not uploaded_file:
                yield f"event: file_progress\ndata: {json.dumps({'error': 'Please provide a file'})}\n\n"
                return

            # Step 1: File Upload
            try:
                file_instance = models.File.objects.create(
                    file=uploaded_file,
                    name=uploaded_file.name,
                    metadata={
                        'content_type': uploaded_file.content_type,
                        'size': uploaded_file.size
                    }
                )
                yield f"event: file_progress\ndata: {json.dumps({'step': 1, 'total': total_steps, 'status': 'File uploaded'})}\n\n"
            except Exception as e:
                yield f"event: file_progress\ndata: {json.dumps({'step': 1, 'error': str(e)})}\n\n"
                return

            # Step 2: Create Temp Local File
            try:
                original_filename = uploaded_file.name  # e.g., "report.pdf"
                _, ext = os.path.splitext(original_filename)  # ".pdf"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    for chunk in file_instance.file.chunks():
                        tmp.write(chunk)
                    tmp.flush()
                    local_path = tmp.name
                yield f"event: file_progress\ndata: {json.dumps({'step': 2, 'total': total_steps, 'status': 'Temp file created'})}\n\n"
            except Exception as e:
                yield f"event: file_progress\ndata: {json.dumps({'step': 2, 'error': str(e)})}\n\n"
                return

            # Step 3: Content Extraction
            try:
                dynamic_loader = DynamicLoader(input_source=local_path, metadata={"user_id" : str(request.user.id), "source_id" : str(file_instance.id), "source" : file_instance.name})
                docs = dynamic_loader.load()
                yield f"event: file_progress\ndata: {json.dumps({'step': 3, 'total': total_steps, 'status': 'Content extracted'})}\n\n"
            except Exception as e:
                yield f"event: file_progress\ndata: {json.dumps({'step': 3, 'error': str(e)})}\n\n"
                return

            # Step 4: Chunking
            try:
                docs = dynamic_loader.splitter.split_documents(docs)
                yield f"event: file_progress\ndata: {json.dumps({'step': 4, 'total': total_steps, 'status': 'Content chunked'})}\n\n"
            except Exception as e:
                yield f"event: file_progress\ndata: {json.dumps({'step': 4, 'error': str(e)})}\n\n"
                return

            # Step 5: Save Chunks
            try:
                file_instance.add_documents(documents=docs, id_suffix = request.user.email.split("@")[0])
                serializer = FileSerializer(file_instance, context={'request': request})
                yield f"event: file_progress\ndata: {json.dumps({'step': 5, 'total': total_steps, 'status': 'Chunks saved', 'file': serializer.data})}\n\n"
            except Exception as e:
                yield f"event: file_progress\ndata: {json.dumps({'step': 5, 'error': str(e)})}\n\n"
                return
            yield f"event: file_progress\ndata: [DONE]\n\n"
            
        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


@method_decorator(csrf_exempt, name='dispatch')
class LLMResponseSSEView(APIView):
    
    def create_human_message(self, conversation_id : str, content_type : str = 'text', content : str | list = '') -> models.Message:
        return models.Message.objects.create_human_message(conversation_id, content_type, content)
        
    def create_assistant_message(self, conversation_id : str, content_type = 'text', content : str | list = '') -> models.Message:
        return models.Message.objects.create_assistant_message(conversation_id, content_type, content= content)
        
        
    def post(self, request, *args, **kwargs):
        user_id = request.user.id
        body = request.data


        conversation_id = body.get("conversation_id")
        query = body.get("query", "Hello")
        attachments = body.get("attachments", [])
        model_name = body.get("model_name", "gemma2-9b-it")
        response_mode = body.get("response_mode", "Scientific")
        self_discussion_flag = body.get("self_discussion", False)
        conversation_metadata = body.get("conversation_metadata", {})
        
        if not query:
            return StreamingHttpResponse(json.dumps({'error': 'Please provide a query'}), content_type="application/json")

        # Get or Create the conversation
        conversation, with_new_conversation = models.Conversation.objects.get_or_create(id=conversation_id, defaults={'user_id': user_id, **conversation_metadata})
        conversation_id = conversation.id
        vector_db = PineconeVectorDB(index_name="sample-index")
            
        # Get the all doc chunks for the conversation
        for attachment in attachments:
            file_instance = models.File.objects.get(id=attachment['id'])
            docs = file_instance.get_documents(metadata={"conversation_id": str(conversation_id)})
            if len(docs):
                vector_db.add_documents(docs)   
                conversation.add_file(file_instance)

            
        messages : list[models.Message] = [
            self.create_human_message(conversation_id, content=query, content_type='text' if len(attachments) == 0 else 'maltilingual'),
            self.create_assistant_message(conversation_id, content='')
        ]
        
        if len(attachments):
            messages[0].content.update({
                "content_type": "maltilingual",
                "attachments": attachments
            })
            messages[0].save()

        s = {
            'user_id': str(user_id),
            'conversation_id': str(conversation_id),
            'vector_db' : vector_db,
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
            tool_index = 0
            
            
            try:
                if with_new_conversation:
                    p = 'conversation'
                    o = 'add'
                    v = ConversationSerializer(conversation).data
                    yield f"event: new_conversation\ndata: {json.dumps({'p' : p, 'o' : o, 'v' : v})}\n\n"
            
                for message, message_data in graph.stream(s, stream_mode='messages'):
                    message : BaseMessage | AIMessage = message
                    message.pretty_print()
                    node = message_data.get('langgraph_node')
                    content = message.content or ""
                    response_metadata = message.response_metadata or {}
                    if hasattr(message, 'usage_metadata') and message.usage_metadata:
                        response_metadata.update(message.usage_metadata)
                    tool_calls = message.tool_calls if hasattr(message, 'tool_calls') else []
                    tool_call_names = [tool_call['name'] for tool_call in tool_calls]
                    
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
                        if not tool_calling:
                            tool_calling = True
                            tool_index = 0
                            messages[1] = self.create_assistant_message(conversation_id, content='')

                        if content:
                            p = f'conversation/message/0/sources/retrived_contexts/{tool_index}'
                            o = "add"
                            v = {'name' : message.name, 'content' : message.content}
                            messages[1].update_retrived_contexts(v)
                            yield f"event: tool_call_response\ndata: {json.dumps({'p' : p, 'o' : o, 'v' : v})}\n\n"
                            tool_index += 1
                        
                messages[1].update_status('complete', metadata=response_metadata)
                messages[1].save()
                yield f"event: done\ndata: [DONE]\n\n"
            
            except Exception as e:
                print(e)
                raise e
                messages[1].update_status('error', metadata=response_metadata)
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')