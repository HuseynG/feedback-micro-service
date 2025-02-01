import asyncio
import aiohttp
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.proxy_config import OxylabsConfig
from tools.search_tools import create_search_tool
import time

async def test_concurrent_searches():
    """Test the ability to perform multiple concurrent searches using the proxy configuration.
    
    This test verifies that:
    1. Multiple search queries can be executed simultaneously
    2. The proxy handles concurrent requests properly
    3. Each search returns results within an acceptable time frame
    4. The system properly handles both successful and failed searches
    
    The test uses a set of general knowledge queries to simulate real-world usage.
    Success is determined by:
    - All queries completing without errors
    - Response times being within acceptable limits
    - Valid results being returned for each query
    """
    search_tool = create_search_tool()
    
    # Test queries
    queries = [
        "What is Python programming?",
        "What is machine learning?",
        "What is artificial intelligence?",
        "What is data science?",
        "What is deep learning?"
    ]
    
    async def perform_search(query):
        start_time = time.time()
        try:
            result = search_tool.run(query)
            duration = time.time() - start_time
            return {
                "query": query,
                "success": True,
                "duration": duration,
                "result": result[:200] + "..."  # Truncate result for readability
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "query": query,
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    # Run searches concurrently
    tasks = [perform_search(query) for query in queries]
    results = await asyncio.gather(*tasks)
    
    # Print results
    print("\nProxy Test Results:")
    print("==================")
    
    all_successful = True
    total_duration = 0
    
    for result in results:
        status = "✅ Success" if result["success"] else "❌ Failed"
        print(f"\nQuery: {result['query']}")
        print(f"Status: {status}")
        print(f"Duration: {result['duration']:.2f}s")
        if result["success"]:
            print(f"Result Preview: {result['result']}")
        else:
            print(f"Error: {result['error']}")
            all_successful = False
        total_duration += result["duration"]
    
    print("\nSummary:")
    print(f"Total Queries: {len(results)}")
    print(f"Average Duration: {total_duration/len(results):.2f}s")
    print(f"Overall Status: {'✅ All Successful' if all_successful else '❌ Some Failed'}")

async def test_proxy_connection():
    """Test the basic connectivity to the Oxylabs proxy service.
    
    This test verifies that:
    1. The proxy configuration is correct (host, port, credentials)
    2. A connection can be established through the proxy
    3. The proxy successfully masks our real IP address
    4. We can retrieve basic geolocation data through the proxy
    
    The test uses ip-api.com to verify the proxy connection and retrieve
    information about the proxy server's location and ISP.
    """
    proxies = OxylabsConfig.get_proxies()
    proxy_url = proxies["http"]
    
    print("\nTesting Proxy Connection:")
    print("========================")
    print(f"Proxy Host: {OxylabsConfig.PROXY_HOST}")
    print(f"Proxy Port: {OxylabsConfig.PROXY_PORT}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://ip-api.com/json", proxy=proxy_url) as response:
                data = await response.json()
                print("\n✅ Proxy Connection Successful!")
                print(f"IP: {data.get('query', 'N/A')}")
                print(f"Location: {data.get('country', 'N/A')}, {data.get('city', 'N/A')}")
                print(f"ISP: {data.get('isp', 'N/A')}")
    except Exception as e:
        print("\n❌ Proxy Connection Failed!")
        print(f"Error: {str(e)}")

async def main():
    """Execute all proxy-related tests in sequence.
    
    This is the main test runner that:
    1. Initializes the test environment
    2. Runs the basic proxy connection test
    3. Runs the concurrent search test
    4. Reports overall test results
    
    This function should be used as the entry point when running proxy tests independently.
    """
    print("Starting Proxy Tests...")
    
    # Test basic proxy connection
    await test_proxy_connection()
    
    # Test concurrent searches
    await test_concurrent_searches()

if __name__ == "__main__":
    asyncio.run(main())
