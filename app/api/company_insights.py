from fastapi import APIRouter
from ai_utils.company_research_agent import CompanyResearchAgent, CompanyResearchConfig
import os
from dotenv import load_dotenv
import logging
from typing import Optional, List
from fastapi import HTTPException

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

router = APIRouter(
    prefix="/company_insights",
    tags=["company_insights"],
    responses={404: {"description": "Not found"}},
)


@router.get("/research")
async def research_company(
    company_name: str,
    include_jobs: bool = False,
    include_reviews: bool = False,
    max_news_items: int = 10,
    max_jobs: int = 7,
    user_interests: Optional[List[str]] = None
):
    """
    **Research a company and gather comprehensive insights.**\n
    Collects company information, recent news, and optionally job listings and reviews.\n
    ---\n
    **Parameters:**\n
        - **company_name**: Name of the company to research\n
        - **include_jobs**: Include job listings (default: False)\n
        - **include_reviews**: Include company reviews (default: False)\n
        - **max_news_items**: Maximum number of news items (default: 10)\n
        - **max_jobs**: Maximum number of jobs when include_jobs is True (default: 7)\n
        - **user_interests**: List of interests to filter jobs (default: None)\n
    \n
    **Returns:**\n
        A dictionary with the following structure:\n
        {\n
            **"status"**: "success" | "error",\n
            **"data"**: {\n
                **"company_info"**: dict,  # Basic company information\n
                **"news"**: list[dict],    # List of news articles\n
                **"jobs"**: list[dict],    # Only if include_jobs=True\n
                **"reviews"**: list[dict]  # Only if include_reviews=True\n
            }\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException**: If an error occurs during the research process\n
    """
    try:
        agent = CompanyResearchAgent(
            azure_endpoint=os.getenv("AZURE_OPENAI_BASE_API_ENDPOINT"),
            azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            serper_api_key=os.getenv("SERPER_API_KEY"),
            tavily_api_key=os.getenv("TAVILY_API_KEY")
        )

        config = CompanyResearchConfig(
            include_jobs=include_jobs,
            include_reviews=include_reviews,
            max_news_items=max_news_items,
            max_jobs=max_jobs
        )

        result = agent.research_company(
            company_name=company_name,
            config=config,
            user_interests=user_interests or []
        )

        return {"status": "success", "data": result}

    except Exception as e:
        logger.error(f"Error researching company {company_name}: {str(e)}")
        return {
            "status": "error",
            "data": {
                "message": f"Error researching company: {str(e)}"
            }
        } 