from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt import ToolInvocation
from .llm import create_llm
from .state import create_initial_state, AgentState
from ..tools.tools import all_tools
from ..config.settings import COMPANY_OVERVIEW_PROMPT, COMPANY_NEWS_PROMPT, COMPANY_REVIEW_PROMPT

def should_continue(state: Dict[str, Any]) -> str:
    """Determine if we should continue or not."""
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        return "tools"
    return END

def create_specialized_workflow(system_prompt: str, tools: list = None):
    """Create a workflow with a specific system prompt and tools.
    
    Args:
        system_prompt (str): System prompt for the agent
        tools (list): List of tools available to the agent (default: all_tools)
    """
    if tools is None:
        tools = all_tools
        
    llm = create_llm()
    
    def call_model(state: Dict[str, Any]):
        """Call the model to get the next action."""
        messages = state["messages"]
        # Insert system message at the beginning if not present
        if not any(isinstance(msg, AIMessage) for msg in messages):
            messages.insert(0, AIMessage(content=system_prompt))
        response = llm.invoke(messages)
        return {"messages": messages + [response]}
    
    # Create the workflow
    workflow = StateGraph(create_initial_state)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolExecutor(tools))
    
    # Add edges
    workflow.add_edge("tools", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    
    # Set the entry point
    workflow.set_entry_point("agent")
    
    return workflow.compile()

def create_overview_workflow():
    """Create workflow for a company overview research."""
    return create_specialized_workflow(
        system_prompt=COMPANY_OVERVIEW_PROMPT,
        tools=all_tools
    )

def create_news_workflow():
    """Create workflow for a company news research."""
    return create_specialized_workflow(
        system_prompt=COMPANY_NEWS_PROMPT,
        tools=all_tools
    )

def create_reviews_workflow():
    """Create workflow for recent reviews of a company."""
    return create_specialized_workflow(
        system_prompt=COMPANY_REVIEW_PROMPT,
        tools=all_tools
    )