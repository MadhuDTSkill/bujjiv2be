import os
from datetime import datetime
from sqlalchemy import create_engine
from langchain_core.messages import trim_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

class Memory:
    def __init__(self, sql_history_obj : SQLChatMessageHistory,  max_tokens: int, token_counter, include_system: bool, allow_partial: bool, start_on: str):
        self.trim_messages = trim_messages(
            max_tokens=max_tokens,
            strategy='last',
            token_counter=token_counter,
            include_system=include_system,
            allow_partial=allow_partial,
            start_on=start_on
        )
        self.sql_history_obj = sql_history_obj
        self.messages = self.get_trimmed_messages()
    
    def get_trimmed_messages(self):
        return self.trim_messages.invoke(self.sql_history_obj.messages)
        
    def get_timestamp(self):
        return datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")

    def add_user_message(self, message: HumanMessage):
        self.sql_history_obj.add_user_message(message)

    def add_ai_message(self, message: AIMessage):
        self.sql_history_obj.add_ai_message(message)
        
    def add_tool_message(self, message: ToolMessage):
        self.sql_history_obj.add_message(message)
        
    def add_message(self, message: BaseMessage):
        self.sql_history_obj.add_message(message)
                
    @classmethod
    def get_memory(cls, session_id:str, user_id:str, max_tokens: int, token_counter, include_system: bool, allow_partial: bool, start_on: str) -> BaseChatMessageHistory:
        engine = create_engine(os.getenv('MEMORY_DATABASE_URL'))
        message_history = SQLChatMessageHistory(session_id=session_id, connection=engine, table_name = user_id)
        message_history_trimmed = cls(message_history, max_tokens, token_counter, include_system, allow_partial, start_on) if len(message_history.messages) > 0 else message_history
        return message_history_trimmed