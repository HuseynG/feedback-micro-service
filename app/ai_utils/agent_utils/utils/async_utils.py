import asyncio
import time
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

async def process_query(graph, query: str, llm, semaphore: asyncio.Semaphore):
    """Process a single query asynchronously with rate limiting."""
    async with semaphore:
        try:
            response = await graph.ainvoke({
                "messages": [HumanMessage(content=query)],
                "llm": llm
            })
            
            for message in response["messages"]:
                if isinstance(message, AIMessage) and message.content:
                    return message.content
            return None
            
        except Exception as e:
            print(f"Error processing query '{query}': {str(e)}")
            raise