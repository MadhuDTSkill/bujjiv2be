import time
from helper.consumers import BaseChatAsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from langchain_groq import ChatGroq
from workflow_graphs.bujji.memory import Memory


class ChatConsumer(BaseChatAsyncJsonWebsocketConsumer):
    groups = []
    

    async def connect(self):        
        """Establishes WebSocket connection and initializes LLM."""
        if await self.user_connect() and await self.graph_connect():
            self.llm = ChatGroq(model="llama-3.1-8b-instant")            
            self.memory = Memory.get_memory(str(self.user.id), str(self.user.id), 4000, self.llm, True, False, 'human')
            

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection."""
        ...

    async def receive_json(self, content, **kwargs):
        """Handles incoming JSON messages."""
        prompt = content.get('prompt', {})
        await self.get_response(prompt)
    
    async def get_response(self, prompt):
        """Processes user prompt and sends response."""
        content = prompt.get('content', '')
        mode = prompt.get('mode', 'Casual')
        if not content:
            await self.send_exception("Prompt is empty")
        await self.send_status("Thinking...")
        self.memory.add_user_message(content)
        response = await self.graph.ainvoke(content, selected_mode=mode)
        response_generator = response.pop('response')
        await self.stream_response(response_generator, response)
        
    async def stream_response(self, generator, response):
        response_chunks = []
        start_time = time.time()
        
        await self.stream('<START>')
        
        for message in generator:
            response_chunks.append(message.content)
            await self.stream(message.content)
            
        await self.stream('<END>')
        end_time = time.time()
        
        final_response = ''.join(response_chunks)
        time_taken = round(end_time - start_time, 2)
        
        data = {
            **response,
            'response': final_response,
            "time_taken": time_taken
        }
        
        status = await self.save_llm_response(data)
        await self.send_status("Resopnse not Saved" if not status else "Response saved successfully")