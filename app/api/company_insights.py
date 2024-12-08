from fastapi import APIRouter
import os
from dotenv import load_dotenv
import logging
from typing import Optional, List
from fastapi import HTTPException
from datetime import datetime
from .insight_schema import CompanyOverview, CompanyNewsList, CompanyReviewList, CompanyNews, CompanyReview
from ai_utils.agent_utils.agent.workflow import create_overview_workflow
from ai_utils.company_insights_utils import CompanyInsightsGenerator
from ai_utils.agent_utils.utils.async_utils import process_query
import asyncio

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

@router.get("/overview/{company_name}", response_model=CompanyOverview)
async def get_company_overview(company_name: str):
    """Get company overview information using AI agent"""
    try:
        # Initialize the workflow and generator
        overview_graph, overview_llm = create_overview_workflow()
        insights_generator = CompanyInsightsGenerator()
        
        # Create query for the agent
        overview_query = f"{company_name} company information, including details about their website, values, vision, size, location, mission, leadership, company type, business nature, and history"
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(100)
        
        # Get raw agent output
        raw_overview = await process_query(overview_graph, overview_query, overview_llm, semaphore)
        
        # Structure the output according to our schema
        structured_overview = await insights_generator.structure_company_overview(raw_overview)
        
        return structured_overview
        
    except Exception as e:
        logger.error(f"Error getting company overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company overview: {str(e)}")

@router.get("/news/{company_name}", response_model=CompanyNewsList)
async def get_company_news(company_name: str):
    """Get company news articles"""
    # Dummy data for demonstration
    return CompanyNewsList(
        news=[
            CompanyNews(
                title="Example Tech Corp Launches New Product",
                post_date=datetime.now(),
                url="https://example.com/news/1"
            ),
            CompanyNews(
                title="Company Expands to European Market",
                post_date=datetime.now(),
                url="https://example.com/news/2"
            ),
            CompanyNews(
                title="Q3 Financial Results Exceed Expectations",
                post_date=datetime.now(),
                url="https://example.com/news/3"
            )
        ]
    )

@router.get("/reviews/{company_name}", response_model=CompanyReviewList)
async def get_company_reviews(company_name: str):
    """Get company reviews from various sources"""
    # Dummy data for demonstration
    return CompanyReviewList(
        reviews=[
            CompanyReview(
                review="Great company culture and work-life balance",
                source="Glassdoor",
                source_url="https://glassdoor.com/example",
                rating=4.5
            ),
            CompanyReview(
                review="Innovative products and strong leadership",
                source="Indeed",
                source_url="https://indeed.com/example",
                rating=4.2
            ),
            CompanyReview(
                review="Excellent customer service and support",
                source="Trustpilot",
                source_url="https://trustpilot.com/example",
                rating=4.8
            )
        ]
    )