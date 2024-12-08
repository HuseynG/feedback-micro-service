import sys
import os
# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# from langchain_community.tools import DuckDuckGoSearchRun
# from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from agent_utils.config.proxy_config import OxylabsConfig
import requests
import urllib3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
from pydantic import Field, BaseModel
from langchain_openai import AzureChatOpenAI
from agent_utils.config.settings import AZURE_CONFIG
from langchain.tools import BaseTool

# Disable SSL warnings for proxy connections
urllib3.disable_warnings()

class SearchVariation(BaseModel):
    """Pydantic model for a search variation"""
    query: str = Field(..., description="The modified search query")
    reason: str = Field(..., description="Reason for this variation")

class SearchVariationsResponse(BaseModel):
    """Pydantic model for the structured output from Azure OpenAI"""
    variations: List[SearchVariation] = Field(
        ..., 
        description="List of search query variations",
        max_items=3
    )

def get_search_variations(query: str) -> List[str]:
    """Generate search variations using Azure OpenAI."""
    llm = AzureChatOpenAI(
        azure_endpoint=AZURE_CONFIG["azure_endpoint"],
        api_key=AZURE_CONFIG["api_key"],
        deployment_name=AZURE_CONFIG["deployment_name"],
        api_version=AZURE_CONFIG["api_version"],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    prompt = f"""Generate 3 different search query variations for the query: "{query}"
    Each variation should help gather different aspects or perspectives of the topic.
    Return the response in the following JSON format:
    {{
        "variations": [
            {{"query": "modified query 1", "reason": "reason for this variation"}},
            {{"query": "modified query 2", "reason": "reason for this variation"}},
            {{"query": "modified query 3", "reason": "reason for this variation"}}
        ]
    }}
    """

    try:
        response = llm.invoke(prompt)
        # Extract the content from the AIMessage
        json_str = response.content
        variations = SearchVariationsResponse.model_validate_json(json_str)
        return [var.query for var in variations.variations]
    except Exception as e:
        print(f"Error generating variations: {str(e)}")
        return [query]  # Return original query if generation fails

class ConcurrentDuckDuckGoSearchRun:
    def __init__(
        self,
        search_wrapper: Any,
        proxies: List[Dict[str, str]],
        workers: int = 10,
        timeout: int = 30,
        total_results: int = 10,
        search_variations: bool = True,
        search_type: str = "text"
    ):
        self.search_wrapper = search_wrapper
        self.proxies = proxies
        self.workers = workers
        self.timeout = timeout
        self.total_results = total_results
        self.search_variations = search_variations
        self.search_type = search_type

    def _format_result(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Format a single search result based on search type."""
        if self.search_type == "news":
            return {
                'resource': result.get('url', ''),
                'heading': result.get('title', ''),
                'text': f"{result.get('body', '')} [Source: {result.get('source', '')} - {result.get('date', '')}]"
            }
        else:  # text search
            return {
                'resource': result.get('href', ''),
                'heading': result.get('title', ''),
                'text': result.get('body', '')
            }

    def _search_with_query(self, query: str) -> List[Dict[str, str]]:
        """Perform search with a single query."""
        try:
            results = self.search_wrapper.run(query)
            # Filter based on correct field names
            return [
                self._format_result(r) for r in results 
                if (self.search_type == "news" and r.get('url')) or 
                   (self.search_type == "text" and r.get('href'))
            ]
        except Exception as e:
            print(f"Search failed for query '{query}': {e}")
            return []

    def run(self, query: str) -> List[Dict[str, str]]:
        """Run the search with query variations if enabled."""
        all_results = []
        queries = [query]

        if self.search_variations:
            variations = get_search_variations(query)
            queries.extend(variations)

        # Use ThreadPoolExecutor for concurrent searches
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_query = {
                executor.submit(self._search_with_query, q): q 
                for q in queries
            }
            
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"Error processing query '{query}': {e}")

        # Deduplicate results based on resource URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result['resource']
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
                if len(unique_results) >= self.total_results:
                    break

        return unique_results[:self.total_results]

def create_search_tool(
    workers: int = 3,
    timeout: int = 30,
    max_results_per_query: int = 10,
    total_results: int = 10,
    search_variations: bool = False,
    time_range: Optional[str] = None,
    search_type: str = "text"
) -> ConcurrentDuckDuckGoSearchRun:
    """Create enhanced DuckDuckGo search tool with concurrent proxy support."""
    try:
        proxy_url = OxylabsConfig.get_proxy_url()
        
        # Initialize DDGS with proxy and timeout
        ddgs = DDGS(
            proxy=proxy_url,  # Changed from proxies to proxy
            timeout=timeout
        )
        
        class DDGSearchWrapper:
            def run(self, query: str) -> List[Dict[str, str]]:
                try:
                    if search_type == "news":
                        return list(ddgs.news(
                            query,
                            region="wt-wt",
                            safesearch="moderate",
                            timelimit=time_range,
                            max_results=max_results_per_query * 2
                        ))
                    else:  # text search (default)
                        return list(ddgs.text(
                            keywords=query,
                            region="wt-wt",
                            safesearch="moderate",
                            timelimit=time_range,
                            max_results=max_results_per_query * 2
                        ))
                except Exception as e:
                    print(f"DDG search failed: {str(e)}")
                    return []

        search_wrapper = DDGSearchWrapper()
        
        return ConcurrentDuckDuckGoSearchRun(
            search_wrapper=search_wrapper,
            proxies=OxylabsConfig.get_proxies(),  # Keep this for other HTTP requests
            workers=workers,
            timeout=timeout,
            total_results=total_results,
            search_variations=search_variations,
            search_type=search_type
        )
    except Exception as e:
        print(f"Failed to create search tool: {e}")
        raise

class DuckDuckGoSearchTool(BaseTool):
    name: str = Field(default="web_search")
    description: str = Field(default="Search the web for current information. Input should be a search query.")
    return_direct: bool = Field(default=False)
    search_instance: ConcurrentDuckDuckGoSearchRun = Field(description="Instance of ConcurrentDuckDuckGoSearchRun")
    
    def _run(self, query: str) -> str:
        """Execute the search."""
        try:
            results = self.search_instance.run(query)
            if not results:
                return "No results found."
            
            # Format results into a readable string
            formatted_results = []
            for idx, result in enumerate(results[:5], 1):
                formatted_results.append(
                    f"{idx}. {result['heading']}\n"
                    f"   URL: {result['resource']}\n"
                    f"   Summary: {result['text']}...\n"
                )
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Search failed: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async implementation of the search."""
        return self._run(query)

if __name__ == "__main__":
    start_time = time.time()
    
    # Test both working search types
    test_queries = [
        ("Apple", "text"),
        ("Apple", "news"),
    ]
    
    for test_query, search_type in test_queries:
        print(f"\n{'='*80}")
        print(f"Testing {search_type.upper()} search with query: '{test_query}'\n")
        
        search_tool = create_search_tool(
            workers=5,
            timeout=20,
            max_results_per_query=5,
            total_results=5,
            search_variations=False,
            time_range="d" if search_type == "news" else None,
            search_type=search_type
        )
        
        try:
            results = search_tool.run(test_query)
            print("\nSearch Results:")
            print(results)
            print("-" * 20)
            
            for idx, result in enumerate(results, 1):
                print(f"\n[Result {idx}]")
                print(f"Title: {result['heading']}")
                print(f"URL: {result['resource']}")
                print(f"Summary: {result['text']}")
                
            print(f"\nTotal results: {len(results)}")
            
        except Exception as e:
            print(f"Error during {search_type} search: {str(e)}")
    
    end_time = time.time()
    print(f"\nTotal time taken: {end_time - start_time:.2f} seconds") 