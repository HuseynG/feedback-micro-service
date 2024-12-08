from langchain_openai import AzureChatOpenAI
from ..config.settings import AZURE_CONFIG
from ..tools.tools import all_tools

def create_llm():
    """Create and configure the LLM."""
    return AzureChatOpenAI(
        azure_endpoint=AZURE_CONFIG["azure_endpoint"],
        api_key=AZURE_CONFIG["api_key"],
        deployment_name=AZURE_CONFIG["deployment_name"],
        api_version=AZURE_CONFIG["api_version"]
    ).bind_tools(all_tools)