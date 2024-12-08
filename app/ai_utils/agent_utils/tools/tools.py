from tools.search_tools import create_search_tool, DuckDuckGoSearchTool
from tools.ai_web_reader import JinaAIWebReaderTool

# Create search instances
news_search_instance = create_search_tool(
    time_range="d",
    search_type="news",
    search_variations=False,
    max_results_per_query=5
)

general_search_instance = create_search_tool(
    search_variations=False,
    max_results_per_query=5
)

# Create LangChain tools
news_search_tool = DuckDuckGoSearchTool(
    name="news_search",
    description="Search for recent news articles and press releases about a company. Input should be a search query.",
    search_instance=news_search_instance
)

general_search_tool = DuckDuckGoSearchTool(
    name="web_search",
    description="Search the web for general information about a company, including company details, websites, and background information. Input should be a search query.",
    search_instance=general_search_instance
)

# Create web reader tool
web_reader_tool = JinaAIWebReaderTool()

# List of all tools
all_tools = [general_search_tool, news_search_tool, web_reader_tool]

# Overview tools
overview_tools = [general_search_tool]

# News tools
news_tools = [news_search_tool]

# Reviews tools
reviews_tools = [general_search_tool, web_reader_tool]