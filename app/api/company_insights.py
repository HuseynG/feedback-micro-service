from fastapi import APIRouter, Query
import os
from dotenv import load_dotenv
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import HTTPException
from ai_utils.company_insights_utils import CompanyInsightsGenerator
import asyncio
from ai_utils.agent_utils.tools.ai_web_reader import read_webpages
# from ai_utils.chatbot_utils import AI_Generator
import httpx
import time
from database.mongodb import mongodb
from api.insight_schema import CompanyInsights

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ai_generator = AI_Generator()
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
        logger.info(f"News results: {results}")
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
        logger.info(f"Reviews response: {reviews_response.json()}")
        return str(reviews_response.json())
    except Exception as e:
        logger.error(f"Error getting company reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company reviews: {str(e)}")

async def fetch_company_overview(company_name: str):
    try:
        start_time = time.time()
        overview_content = await company_insights_generator.generate_company_overview(company_name)
        end_time = time.time()
        logger.info(f"Total time taken (fetch_company_overview): {end_time - start_time} seconds")
        return overview_content
    except Exception as e:
        logger.error(f"Error getting company overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company overview: {str(e)}")

async def fetch_company_role(company_name: str, user_role: str=None, location: str=None) -> str:
    try:
        start_time = time.time()
        role_content = await company_insights_generator.generate_company_role(company_name, user_role, location)
        end_time = time.time()
        logger.info(f"Total time taken (fetch_company_role): {end_time - start_time} seconds")
        return role_content
    except Exception as e:
        logger.error(f"Error getting company role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company role: {str(e)}")
    
async def fetch_company_interview(company_name: str, user_role: str=None, location: str=None) -> str:
    try:
        start_time = time.time()
        interview_content = await company_insights_generator.generate_company_interview(company_name, user_role, location)
        end_time = time.time()
        logger.info(f"Total time taken (fetch_company_interview): {end_time - start_time} seconds")
        return interview_content
    except Exception as e:
        logger.error(f"Error getting company interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company interview: {str(e)}")

async def get_company_insights_(company_name: str, user_role: str=None, location: str=None):
    start_time = time.time()
    
    # overview_content, role_content, interview_content, news_content, reviews_content = await asyncio.gather(
    #     fetch_company_overview(company_name),
    #     fetch_company_role(company_name, user_role, location),
    #     fetch_company_interview(company_name, user_role, location),
    #     fetch_company_news(company_name),
    #     fetch_company_reviews(company_name),
    #     return_exceptions=True
    # )
    # end_time = time.time()
    # logger.info(f"Total time taken: {end_time - start_time} seconds")

    # raw_content = {
    #     "user_query": {
    #         "company_name": company_name,
    #         "user_role": user_role,
    #         "location": location
    #     },
    #     "overview": overview_content,
    #     "news": news_content,
    #     "reviews": reviews_content,
    #     "role": role_content,
    #     "interview": interview_content
    # }
    # loading dummy pickled for testing purposes. 
    import pickle
    with open("company_insights_raw_content.pkl", "rb") as f:
        raw_content = pickle.load(f)
    
    return company_insights_generator.structure_company_insights(str(raw_content))

async def get_cached_insights(company_name: str, user_role: Optional[str] = None, location: Optional[str] = None) -> Optional[dict]:
    """
    Retrieve cached company insights from MongoDB if they exist.
    
    Args:
        company_name (str): Name of the company
        user_role (Optional[str]): Role of the user
        location (Optional[str]): Location of the user
        
    Returns:
        Optional[dict]: Cached insights data if found, None otherwise
    """
    try:
        cache_query = {
            "company_name": company_name,
            "user_role": user_role,
            "location": location
        }
        
        cached_insights = await mongodb.company_insights.find_one(cache_query)
        
        if cached_insights:
            logger.info("Found cached insights, returning from cache")
            return cached_insights["insights_data"]
            
        return None
    except Exception as e:
        logger.error(f"Error retrieving cached insights: {str(e)}")
        return None

@router.get("/insight")
async def get_company_insights(
    company_name: str = Query(..., description="Name of the company to get insights for"),
    user_role: str = Query(None, description="Role of the user to get insights for"),
    location: str = Query(None, description="Location of the user to get insights for")
):
    """Get company overview information using AI agent"""
    try:
        # Check cache first
        cached_result = await get_cached_insights(company_name, user_role, location)
        if cached_result:
            return cached_result
            
        # If not in cache, generate new insights
        insights_data = await get_company_insights_(company_name, user_role, location)
        logger.info(f"Insights data: {insights_data}")
        
        # Cache the results - insights_data already contains user query info
        insights_dict = insights_data.dict()
        insights_dict["createdAt"] = datetime.utcnow()  # Add TTL field
        mongodb.company_insights.insert_one(insights_dict)
        
        return insights_data
    except Exception as e:
        logger.error(f"Error getting company overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company overview: {str(e)}")