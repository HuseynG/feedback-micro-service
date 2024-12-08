import aiohttp
import asyncio
from dotenv import load_dotenv
import os
import time
from typing import List, Dict, Union
from dataclasses import dataclass
from langchain.tools import BaseTool
import json

load_dotenv()

@dataclass
class WebPageResult:
    url: str
    content: str
    execution_time: float
    success: bool
    error: str = ""
    
    def to_dict(self):
        return {
            "url": self.url,
            "content": self.content,
            "execution_time": self.execution_time,
            "success": self.success,
            "error": self.error
        }

async def read_webpage_async(session: aiohttp.ClientSession, query_url: str) -> WebPageResult:
    """
    Asynchronously read a webpage using Jina AI's API.
    
    Args:
        session: aiohttp client session
        query_url: The URL to read
        
    Returns:
        WebPageResult: Contains the result of the web page fetch
    """
    start_time = time.time()
    jina_url = f'https://r.jina.ai/{query_url}'
    
    try:
        async with session.get(jina_url) as response:
            content = await response.text()
            execution_time = time.time() - start_time
            return WebPageResult(
                url=query_url,
                content=content,
                execution_time=execution_time,
                success=True
            )
    except Exception as e:
        execution_time = time.time() - start_time
        return WebPageResult(
            url=query_url,
            content="",
            execution_time=execution_time,
            success=False,
            error=str(e)
        )

async def read_webpages(urls: List[str], max_workers: int = 100) -> List[WebPageResult]:
    """
    Read multiple webpages concurrently with a limit on concurrent workers.
    
    Args:
        urls: List of URLs to process
        max_workers: Maximum number of concurrent workers (default: 100)
        
    Returns:
        List[WebPageResult]: Results for each URL
    """
    jina_api_key = os.getenv("JINA_API_KEY")
    if not jina_api_key:
        raise ValueError("JINA_API_KEY not found in environment variables")

    headers = {
        'Authorization': f'Bearer {jina_api_key}'
    }
    
    connector = aiohttp.TCPConnector(limit=max_workers)
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        tasks = [read_webpage_async(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        
    return results

def print_results(results: List[WebPageResult]) -> None:
    """Print a summary of the results."""
    print("\nResults Summary:")
    print("-" * 50)
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"Total URLs processed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Average execution time: {sum(r.execution_time for r in results)/len(results):.2f} seconds")
    
    if failed:
        print("\nFailed URLs:")
        for result in failed:
            print(f"- {result.url}: {result.error}")

class JinaAIWebReaderTool(BaseTool):
    name: str = "jina_web_reader"
    description: str = """JinaAI Reader tool: Read web pages using Jina AI's API. 
    Input should be either a single URL as a string or a list of URLs.
    For a single URL, returns the page content.
    For multiple URLs, returns a list of results with content and metadata."""
    
    def _run(self, urls: Union[str, List[str]]) -> Union[str, List[Dict]]:
        # Convert single URL to list
        if isinstance(urls, str):
            urls = [urls]
            
        # Run async code in sync context
        results = asyncio.run(read_webpages(urls))
        
        # Return single result content for single URL
        if len(urls) == 1:
            return results[0].content if results[0].success else ""
        
        # Return full results for multiple URLs
        return [r.to_dict() for r in results]
    
    async def _arun(self, urls: Union[str, List[str]]) -> Union[str, List[Dict]]:
        # Convert single URL to list
        if isinstance(urls, str):
            urls = [urls]
            
        results = await read_webpages(urls)
        
        # Return single result content for single URL
        if len(urls) == 1:
            return results[0].content if results[0].success else ""
        
        # Return full results for multiple URLs
        return [r.to_dict() for r in results]

if __name__ == "__main__":
    # Example usage with multiple URLs
    search_query = "apple"
    test_urls = [
        f"https://www.bing.com/jobs?q={search_query}",
        # f"https://www.google.com/search?q={search_query}%20jobs&jbr=sep:0&udm=8"
        # f"https://www.bing.com/news/search?q={search_query}",
        # f"https://www.bing.com/search?q={search_query}"
        # "https://www.google.com",
        # "https://www.github.com",
        # "https://www.microsoft.com"
    ]
    
    async def main():
        start_time = time.time()
        results = await read_webpages(test_urls, max_workers=100)
        total_time = time.time() - start_time
        
        print_results(results)
        print(f"\nTotal execution time: {total_time:.2f} seconds")
        
        # Print full content for successful results if needed
        for result in results:
            if result.success:
                print(f"\nContent from {result.url}:")
                # print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
                print(result.content)

    
    asyncio.run(main())
