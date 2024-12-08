import asyncio
import concurrent.futures
import platform
import time
from agent.workflow import create_overview_workflow, create_news_workflow, create_reviews_workflow
from utils.async_utils import process_query
from utils.logger import log_agent_action

async def main():
    # Create both workflows
    log_agent_action("system", "Initializing agent workflows...")
    overview_graph, overview_llm = create_overview_workflow()
    reviews_graph, reviews_llm = create_reviews_workflow()

    # Test company name
    company = "Rider Levett Bucknall"
    log_agent_action("system", f"Starting research for company: {company}")
    
    # Create queries for both agents
    overview_query = f"{company} company information, address, website, vision"
    reviews_query = f"{company} recent reviews"
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(100)

    log_agent_action("system", "Starting parallel company research...")
    start_time = time.time()

    # Process both queries in parallel
    overview_content, reviews_content = await asyncio.gather(
        process_query(overview_graph, overview_query, overview_llm, semaphore),
        process_query(reviews_graph, reviews_query, reviews_llm, semaphore),
        return_exceptions=True
    )

    # Print results with logging
    log_agent_action("overview", "=== Company Overview ===")
    if isinstance(overview_content, Exception):
        log_agent_action("overview", f"Error: {overview_content}")
    else:
        log_agent_action("overview", overview_content)
    
    log_agent_action("reviews", "=== Recent Reviews ===")
    if isinstance(reviews_content, Exception):
        log_agent_action("reviews", f"Error: {reviews_content}")
    else:
        log_agent_action("reviews", reviews_content)

    total_duration = time.time() - start_time
    log_agent_action("system", f"Total parallel research time: {total_duration:.2f} seconds")

if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=100)
    loop.set_default_executor(executor)
    
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
        executor.shutdown() 