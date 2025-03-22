import operator
from typing import Sequence
from typing import TypedDict
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import BaseMessage


class WorkFlowState(TypedDict):
    _verbose : bool
    _consumer: object
    user_query: str
    selected_mode: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    final_response : dict