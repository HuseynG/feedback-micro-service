from fastapi import APIRouter, Query
import os
from dotenv import load_dotenv
import logging
from typing import Optional, List
from fastapi import HTTPException
from datetime import datetime
from ai_utils.company_insights_utils import CompanyInsightsGenerator
import asyncio
from ai_utils.agent_utils.tools.ai_web_reader import read_webpages
from ai_utils.chatbot_utils import AI_Generator
import httpx

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ai_generator = AI_Generator()
company_insights_generator = CompanyInsightsGenerator()

router = APIRouter(
    prefix="/company_insights",
    tags=["company_insights"],
    responses={404: {"description": "Not found"}},
)

async def fetch_company_news(company_name: str) -> str:
    try:
        news_url = f"https://www.bing.com/news/search?q={company_name}"
        results = await read_webpages([news_url])
        if not results[0].success:
            raise HTTPException(status_code=500, detail="Failed to fetch news")
        return "".join(r.content for r in results)
    except Exception as e:
        logger.error(f"Error getting company news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company news: {str(e)}")

async def fetch_company_reviews(company_name: str) -> dict:
    try:
        url = "https://real-time-glassdoor-data.p.rapidapi.com/company-search"
        headers = {
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
            "x-rapidapi-host": "real-time-glassdoor-data.p.rapidapi.com"
        }
        
        # First API call to get company_id
        search_response = await httpx.AsyncClient().get(
            url, 
            headers=headers, 
            params={"query": company_name, "limit": "10"}
        )
        company_id = search_response.json()['data'][0]['company_id']
        
        # Second API call to get reviews
        reviews_url = "https://real-time-glassdoor-data.p.rapidapi.com/company-reviews"
        reviews_params = {
            "company_id": company_id,
            "page": "1",
            "sort": "POPULAR",
            "language": "en",
            "only_current_employees": "false",
            "extended_rating_data": "false"
        }
        
        reviews_response = await httpx.AsyncClient().get(
            reviews_url, 
            headers=headers, 
                params=reviews_params
            )
        return str(reviews_response.json())
    except Exception as e:
        logger.error(f"Error getting company reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company reviews: {str(e)}")

async def fetch_company_overview(company_name: str):
    try:
        return await company_insights_generator.generate_company_overview(company_name)
    except Exception as e:
        logger.error(f"Error getting company overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company overview: {str(e)}")

async def fetch_company_role(company_name: str, user_role: str=None, location: str=None) -> str:
    try:
        return await company_insights_generator.generate_company_role(company_name, user_role, location)
    except Exception as e:
        logger.error(f"Error getting company role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company role: {str(e)}")
    
async def fetch_company_interview(company_name: str, user_role: str=None, location: str=None) -> str:
    try:
        return await company_insights_generator.generate_company_interview(company_name, user_role, location)
    except Exception as e:
        logger.error(f"Error getting company interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company interview: {str(e)}")

async def get_company_insights_(company_name: str, user_role: str=None, location: str=None):
    # Gather all data concurrently
    overview_task = fetch_company_overview(company_name)
    role_task = fetch_company_role(company_name, user_role, location)
    interview_task = fetch_company_interview(company_name, user_role, location)


    # news_task = fetch_company_news(company_name) # RecentNews
    # reviews_task = fetch_company_reviews(company_name) 
    
    
    # # # Wait for all tasks to complete
    # overview_content, news_content, reviews_content = await asyncio.gather(
    #     overview_task,
    #     news_task,
    #     reviews_task,
    #     return_exceptions=True
    # )
    
    overview_content, role_content, interview_content = await asyncio.gather(
        overview_task,
        role_task,
        interview_task,
        return_exceptions=True
    )
    
    news_content = None
    reviews_content = None
    
    raw_content = {
        "overview": overview_content,
        "news": news_content,
        "reviews": reviews_content,
        "role": role_content,
        "interview": interview_content
    }
    
    return company_insights_generator.structure_company_insights(str(raw_content))

@router.get("/insight")
async def get_company_insights(
    company_name: str = Query(..., description="Name of the company to get insights for"),
    user_role: str = Query(None, description="Role of the user to get insights for"),
    location: str = Query(None, description="Location of the user to get insights for")
):
    """Get company overview information using AI agent"""
    try:
        return await get_company_insights_(company_name, user_role, location)
    except Exception as e:
        logger.error(f"Error getting company overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company overview: {str(e)}")