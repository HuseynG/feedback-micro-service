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
import requests

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

@router.get("/overview/{company_name}")
async def get_company_overview(company_name: str):
    """Get company overview information using AI agent"""
    try:
        url = "https://linkedin-data-api.p.rapidapi.com/get-company-insights"

        querystring = {"username":company_name}

        headers = {
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
            "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)

        return response.json()
        
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

@router.get("/reviews/{company_name}",)
async def get_company_reviews(company_name: str):
    """Get company reviews from various sources"""
    
    url = "https://real-time-glassdoor-data.p.rapidapi.com/company-search"

    querystring = {"query":company_name,"limit":"10"}

    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "real-time-glassdoor-data.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    company_id = response.json()['data'][0]['company_id']
    
    url = "https://real-time-glassdoor-data.p.rapidapi.com/company-reviews"

    querystring = {"company_id":company_id,"page":"1","sort":"POPULAR","language":"en","only_current_employees":"false","extended_rating_data":"false"}

    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "real-time-glassdoor-data.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()