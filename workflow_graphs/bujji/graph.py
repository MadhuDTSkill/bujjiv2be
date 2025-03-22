import time
import groq
from typing import List
from langgraph.graph import StateGraph, START, END
from typing import Annotated
from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from .prompts import BUJJI_SYSTEM_MESSAGE
from .schemas import WorkFlowState
from .tools import calculator_tool, web_url_tool, duckduckgo_search_tool
from auth_app.models import User
from .memory import Memory
from .vector_db import PineconeVectorDB
from langchain_core.tools import tool
from langchain_core.documents import Document



class BujjiThinkWorkflow:
    def __init__(self, user : User, consumer : object, llm : ChatGroq, verbose=True):
        self.user = user
        self.consumer = consumer
        self.llm : ChatGroq = llm
        self.memory = Memory.get_memory(str(user.id), str(self.user.id), 4000, self.llm, True, False, 'human')
        self.verbose = verbose
        self.pinecone_vector_db = PineconeVectorDB(index_name=str(self.user.id))
        self.vector_db_retriever : Runnable = self.pinecone_vector_db.as_retriever()
        self.tools : List[BaseTool] = [calculator_tool, web_url_tool, duckduckgo_search_tool, self._pinecone_vector_db_user_history]        
        self.tool_llm = llm.bind_tools(self.tools)


    async def _verbose_print(self, message: str, state : WorkFlowState):
        if self.verbose:
            print(f"\n\033[92m[VERBOSE] {message}\033[0m")


    async def _yield_status(self, message : str, state : WorkFlowState):
        from helper.consumers import BaseChatAsyncJsonWebsocketConsumer
        consumer : BaseChatAsyncJsonWebsocketConsumer = state['_consumer']
        await consumer.send_status(message)

    
    async def _get_history(self):
        return self.memory.messages
      
            
    async def _get_messages(self, new_message : str):
        history = await self._get_history()
        messages = [
            SystemMessage(content=BUJJI_SYSTEM_MESSAGE),
            *history,
            HumanMessage(content=new_message)
        ]        
        return messages
    
    @tool("Pincone Vector DB User History")
    def _pinecone_vector_db_user_history(self, query : Annotated[str, "Query to search the Pinecone Vector DB"]) -> str:
        """
            This tool is used to get the user's history from the Pinecone Vector DB.
        """
        
        result : list[Document] = self.vector_db_retriever.invoke({"query": query})
        return "\n".join([f"{i+1}. {doc.page_content}" for i, doc in enumerate(result)])


    async def _build_workflow(self):
        builder = StateGraph(WorkFlowState)
        
        builder.add_node("Bujji",self.bujji)
        builder.add_node("Tool Call Handler", self.tool_call_handler)
        builder.add_node("Extra Knowledge & Tool Call", self.extra_knowledge_and_tool_call)
        builder.add_node("Final Response", self.final_response)
        
        builder.set_entry_point("Tool Call Handler")
        builder.add_edge("Extra Knowledge & Tool Call", "Bujji")
        builder.add_edge("Bujji", "Final Response")
        builder.set_finish_point("Final Response")
        
        builder.add_conditional_edges(
            "Tool Call Handler",
            lambda state: "Need Tool Calls" if state["messages"][-1].tool_calls else "Submit Response",
            {
                "Need Tool Calls": "Extra Knowledge & Tool Call",
                "Submit Response" : "Bujji",
            }
        )
        
        return builder.compile()
    
    
    async def tool_call_handler(self, state: WorkFlowState) -> dict:
        user_query = state["user_query"]

        execution_prompt = f"""
            - You are a tool executor responsible for determining if any external tools are needed to answer the user query.
            - Only suggest tools if the query explicitly requires real-time information, external data retrieval, or execution beyond your general knowledge.
            - If the response can be generated using general knowledge without real-time data or external tools, return "No tools".
            - Do NOT suggest tools for queries that can be answered directly.

            User Query: {user_query}
            Tools Available: {[tool.name for tool in self.tools]}
        """

        response = await self.tool_llm.ainvoke(await self._get_messages(execution_prompt))
        
        await self._verbose_print(f"Tool Call Handler Response: {response}", state)

        return {
            "messages": [response]
        }


    
    def extra_knowledge_and_tool_call(self, state: WorkFlowState) -> dict:

        last_message = state['messages'][-1]
                

        tools_by_name = {tool.name: tool for tool in self.tools}
        tool_messages = []

        for tool_call in last_message.tool_calls:
            tool = tools_by_name.get(tool_call["name"])
            if not tool:
                continue

            retries = 2
            for attempt in range(1, retries + 1):
                try:
                    observation = tool(**tool_call["args"])  
                    tool_messages.append(ToolMessage(
                        content=observation,
                        name=tool.name,
                        tool_call_id=tool_call["id"],
                    ))
                    break  

                except Exception as e:
                    if attempt == retries:
                        error_message = f"Error: Tool invocation failed after {retries}/2 attempts. Error: {str(e)}"
                        tool_messages.append(ToolMessage(
                            content=error_message,
                            name=tool.name,
                            tool_call_id=tool_call["id"],
                        ))
        
        return {
            "messages": tool_messages,
        }


    async def bujji(self, state: WorkFlowState) -> dict:
        await self._verbose_print("Loading ..", state)
        await self._yield_status("🔍 Loading...", state)
        
        user_query = state["user_query"]
        ai_message = self.llm.stream(
            await self._get_messages(user_query)
        )
        return {
            "messages" : [ai_message]
        }        
        

    async def final_response(self, state: WorkFlowState) -> dict:        
        messages = state.get('messages', [])
        last_message = state.get('messages', [])[-1]
        tool_messages = [ {"Name" : message.name, "Response" : message.content} for message in messages if isinstance(message, ToolMessage)]
        final_response = last_message

        final_response = {
            "user" : str(self.user.id),
            "prompt": state["user_query"],
            "response": final_response,
            "tool_responses": tool_messages,
        }
        self.pinecone_vector_db.add_documents(text=f"Chatbot Response: {final_response}")
        
        return {"final_response": final_response}
    
    

    async def ainvoke(self, user_query: str, selected_mode: str = "Casual") -> str:
        self.memory.add_user_message(user_query)
        initial_state = {
            "user_query": user_query, 
            "selected_mode": selected_mode,
            "_consumer" : self.consumer,
        }
        start_time = time.time()

        await self._verbose_print(f"Running with user query: {user_query} and selected mode: {selected_mode}", initial_state)
        final_state = await self.workflow.ainvoke(initial_state)

        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        # final_state["final_response"]["time_taken"] = time_taken
        # self.memory.add_ai_message(final_state["final_response"]["response"])
        return final_state["final_response"]
   
    
    async def get_flow_image(self):
        graph_png = self.workflow.get_graph(xray=True).draw_mermaid_png()
        image_file = "BujjiThinkWorkflow.png"
        with open(image_file, "wb") as file:
            file.write(graph_png)
            
        print(f"Graph saved as {image_file}")
        
        
    @classmethod
    async def init_graph(cls, *args, **kwargs):
        graph = cls(*args, **kwargs)
        graph.workflow = await graph._build_workflow()
        # await graph.get_flow_image()
        return graph

        
