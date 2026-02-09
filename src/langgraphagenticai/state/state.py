from typing_extensions import TypedDict,List, NotRequired
from langgraph.graph.message import add_messages
from typing import Annotated


class State(TypedDict):
    """
    Represent the structure of the state used in graph
    """
    messages: Annotated[List,add_messages]
    
    # --- Brew Guide Agent loop controls (optional keys) ---
    tool_calls_count: NotRequired[int]
    revision_count: NotRequired[int]
    needs_revision: NotRequired[bool]