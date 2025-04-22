import operator
from typing import Sequence
from typing import TypedDict
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langchain_core.tools import BaseTool
from langgraph.graph.message import add_messages
from .memory import Memory
from .vector_dbs import BaseVectorDB


class WorkFlowState(TypedDict):
    _verbose : bool = False
    response_mode : str = "Auto" # "Casual", "Scientific", "Story", "Kids", "Auto"
    self_discussion : bool = False # True, False
    pre_tools : list = [] # "Example Tool", "No Tool"
    model_name : str = "gemma2-9b-it" # "gemma2-9b-it", "Auto"
    model : ChatGroq
    memory : Memory
    vector_db : BaseVectorDB
    user_id : str # uuid
    conversation_id : str # uuid
    tools : Sequence[BaseTool] = [] # [BaseTool]
    user_query : str = ""
    messages: Annotated[Sequence[BaseMessage], add_messages] = []
    memory_messages : Annotated[Sequence[BaseMessage], add_messages] = []
    new_messages : Annotated[Sequence[BaseMessage], add_messages] = []

    