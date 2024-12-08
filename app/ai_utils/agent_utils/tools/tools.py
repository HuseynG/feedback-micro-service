from langchain.tools import Tool
from .search_tools import web_search
from .ai_web_reader import read_webpage

# Create tools
all_tools = [
    Tool(
        name="web_search",
        description="Search the web for information about a company",
        func=web_search,
    ),
    Tool(
        name="read_webpage",
        description="Read and extract information from a webpage",
        func=read_webpage,
    ),
]