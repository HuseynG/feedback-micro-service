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

@router.get("/hello")
async def get_hello_world():
    """
    A simple hello world endpoint for testing company insights.
    """
    return {"message": "Hello from Company Insights!"} 

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
    Research a company using the CompanyResearchAgent.
    
    Args:
        company_name: Name of the company to research
        include_jobs: Whether to include job listings
        include_reviews: Whether to include company reviews
        max_news_items: Maximum number of news items to return
        max_jobs: Maximum number of jobs to return
        user_interests: List of user interests for job matching
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