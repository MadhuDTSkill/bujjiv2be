import asyncio
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from uuid import uuid4  
from channels.db import database_sync_to_async
from chats_app import serializers
from langchain_groq import ChatGroq
from workflow_graphs.bujji.graph import BujjiThinkWorkflow


class BaseChatAsyncJsonWebsocketConsumer(AsyncJsonWebsocketConsumer):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
             
                
    async def user_connect(self):
        user = self.scope.get('user')
        if user is None:
            await self.close(code=4403)  
            return False
        else:
            await self.accept()
            self.user = user
            return True            
        
    async def graph_connect(self):
        try :
            llm_instance = ChatGroq(model="llama-3.1-8b-instant")
            self.graph = await BujjiThinkWorkflow.init_graph(
                user = self.user,
                consumer = self,
                llm = llm_instance,
            )
            return True
        except Exception as e:
            await self.send_exception(str(e))
            return False

    @database_sync_to_async
    def save_llm_response(self, data):
        serializer = serializers.LLMResponseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return True
        print(serializer.errors)
        return False
    
    
    async def send_exception(self, msg=''):
        await self.send_json({
            'type' : "exception",
            "data" : {
                'content': msg
            }
        })
        await self.close()
        
    async def send_status(self, msg = ''):
        if len(msg) > 100:
            msg = msg[:100] + '...'
        await self.send_json({
            'type' : "status",
            "data" : {
              'content': msg
            }
        })
    
    async def stream(self, chunk):
        await self.send_json({
            'type' : "stream",
            'data': chunk
        })
    
    async def send_json(self, *args, **kwargs):
        await asyncio.sleep(0.1)
        await super().send_json(*args, **kwargs)

    @classmethod
    async def generate_random_id(cls):
        return str(uuid4())