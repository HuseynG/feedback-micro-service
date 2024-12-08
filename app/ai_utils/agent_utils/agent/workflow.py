from typing import Literal, List
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from tools.tools import all_tools, overview_tools, news_tools, reviews_tools
from agent.state import AgentState
from agent.llm import create_llm
from config.settings import COMPANY_OVERVIEW_PROMPT, COMPANY_NEWS_PROMPT, COMPANY_REVIEW_PROMPT
from langchain_core.messages import SystemMessage
from langchain.tools import BaseTool

def should_continue(state: AgentState) -> Literal["tools", END]:
    """Determine if we should continue or not."""
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return END

def create_specialized_workflow(system_prompt: str, tools: List[BaseTool] = all_tools):
    """Create a workflow with a specific system prompt and tools.
    
    Args:
        system_prompt (str): The system prompt to use for the agent
        tools (List[BaseTool]): List of tools available to the agent (default: tools_list)
    """
    llm = create_llm()
    
    def call_model(state: AgentState):
        """Call the model to get the next action."""
        messages = state["messages"]
        # Insert system message at the beginning if not present
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages.insert(0, SystemMessage(content=system_prompt))
        response = state["llm"].invoke(messages)
        return {"messages": [response]}
    
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))  # Use the provided tools
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    
    return workflow.compile(), llm

def create_overview_workflow():
    """Create workflow for a company overview research."""
    return create_specialized_workflow(system_prompt=COMPANY_OVERVIEW_PROMPT, tools=overview_tools)

def create_news_workflow():
    """Create workflow for a company news research."""
    return create_specialized_workflow(system_prompt=COMPANY_NEWS_PROMPT, tools=news_tools) 
def create_reviews_workflow():
    """Create workflow for recent reviews of a company."""
    return create_specialized_workflow(system_prompt=COMPANY_REVIEW_PROMPT, tools=reviews_tools)