from typing import Dict, Any, List
from langchain_core.messages import BaseMessage

def create_initial_state() -> Dict[str, Any]:
    """Create the initial state for the agent."""
    return {
        "messages": [],  # List to store conversation messages
        "llm": None,  # Will be set when creating the workflow
        "tools": [],  # List of available tools
        "current_task": None,  # Current task being processed
        "results": {},  # Store results from tool executions
    }

class AgentState(Dict[str, Any]):
    """State class for the agent."""
    messages: List[BaseMessage]
    llm: Any
    tools: List[Any]
    current_task: str | None
    results: Dict[str, Any]