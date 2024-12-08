from typing import Any
from langgraph.graph.message import MessagesState

class AgentState(MessagesState):
    """Extend MessagesState to include llm"""
    llm: Any 