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
import re
from database.mongodb import mongodb
from api.insight_schema import CompanyInsights
from bson import json_util
import json

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
    tags=["Company Insights"],
    responses={404: {"description": "Not found"}},
)

async def fetch_company_news(company_name: str) -> str:
    """
    **Fetch recent news articles about a company using Bing News.**\n
    \n
    **Parameters:**\n
        - **company_name**: Name of the company to fetch news for\n
    \n
    **Returns:**\n
        str: Concatenated news articles content\n
    \n
    **Raises:**\n
        - **HTTPException (500)**: If news fetching fails\n
    """
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
    """
    **Fetch company reviews and ratings from various sources.**\n
    \n
    **Parameters:**\n
        - **company_name**: Name of the company to fetch reviews for\n
    \n
    **Returns:**\n
        dict: Company reviews and ratings containing:\n
        {\n
            **"overall_rating"**: float,     # Average rating across platforms\n
            **"total_reviews"**: int,        # Total number of reviews\n
            **"review_summary"**: str        # AI-generated summary of reviews\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (500)**: If review fetching fails\n
    """
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

async def fetch_company_overview(company_name: str) -> dict:
    """
    **Fetch general overview information about a company.**\n
    \n
    **Parameters:**\n
        - **company_name**: Name of the company to fetch overview for\n
    \n
    **Returns:**\n
        dict: Company overview containing:\n
        {\n
            **"description"**: str,          # Company description\n
            **"industry"**: str,             # Industry sector\n
            **"size"**: str,                 # Company size range\n
            **"headquarters"**: str,         # Company headquarters location\n
            **"founded"**: str               # Year founded\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (500)**: If overview fetching fails\n
    """
    try:
        start_time = time.time()
        overview_content = await company_insights_generator.generate_company_overview(company_name)
        end_time = time.time()
        logger.info(f"Total time taken (fetch_company_overview): {end_time - start_time} seconds")
        return overview_content
    except Exception as e:
        logger.error(f"Error getting company overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company overview: {str(e)}")

async def fetch_company_role(company_name: str, user_role: str=None, location: str=None) -> dict:
    """
    **Fetch role-specific information about a company.**\n
    \n
    **Parameters:**\n
        - **company_name**: Name of the company\n
        - **user_role**: Optional role to get specific information for\n
        - **location**: Optional location to get regional information\n
    \n
    **Returns:**\n
        dict: Role-specific information containing:\n
        {\n
            **"salary_range"**: str,         # Typical salary range for the role\n
            **"requirements"**: List[str],    # Key requirements for the role\n
            **"benefits"**: List[str],        # Company benefits\n
            **"culture"**: str                # Company culture description\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (500)**: If role information fetching fails\n
    """
    try:
        start_time = time.time()
        role_content = await company_insights_generator.generate_company_role(company_name, user_role, location)
        end_time = time.time()
        logger.info(f"Total time taken (fetch_company_role): {end_time - start_time} seconds")
        return role_content
    except Exception as e:
        logger.error(f"Error getting company role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company role: {str(e)}")
    
async def fetch_company_interview(company_name: str, user_role: str=None, location: str=None) -> dict:
    """
    **Fetch interview-related information about a company.**\n
    \n
    **Parameters:**\n
        - **company_name**: Name of the company\n
        - **user_role**: Optional role to get specific interview info for\n
        - **location**: Optional location for regional interview practices\n
    \n
    **Returns:**\n
        dict: Interview information containing:\n
        {\n
            **"process"**: str,              # Interview process description\n
            **"common_questions"**: List[str], # Frequently asked questions\n
            **"tips"**: List[str],            # Interview preparation tips\n
            **"duration"**: str               # Typical interview process duration\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (500)**: If interview information fetching fails\n
    """
    try:
        start_time = time.time()
        interview_content = await company_insights_generator.generate_company_interview(company_name, user_role, location)
        end_time = time.time()
        logger.info(f"Total time taken (fetch_company_interview): {end_time - start_time} seconds")
        return interview_content
    except Exception as e:
        logger.error(f"Error getting company interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company interview: {str(e)}")

async def get_company_insights_(company_name: str, user_role: str=None, location: str=None) -> dict:
    """
    **Generate comprehensive company insights by aggregating various data sources.**\n
    \n
    **Parameters:**\n
        - **company_name**: Name of the company\n
        - **user_role**: Optional role to get specific insights for\n
        - **location**: Optional location for regional insights\n
    \n
    **Returns:**\n
        dict: Comprehensive company insights containing:\n
        {\n
            **"overview"**: dict,            # General company overview\n
            **"news"**: str,                 # Recent news articles\n
            **"reviews"**: dict,             # Company reviews and ratings\n
            **"role_info"**: dict,           # Role-specific information\n
            **"interview_info"**: dict       # Interview-related information\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (500)**: If insights generation fails\n
    """
    start_time = time.time()
    
    overview_content, role_content, interview_content, news_content, reviews_content = await asyncio.gather(
        fetch_company_overview(company_name),
        fetch_company_role(company_name, user_role, location),
        fetch_company_interview(company_name, user_role, location),
        fetch_company_news(company_name),
        fetch_company_reviews(company_name),
        return_exceptions=True
    )
    end_time = time.time()
    logger.info(f"Total time taken: {end_time - start_time} seconds")

    raw_content = {
        "user_query": {
            "company_name": company_name,
            "user_role": user_role,
            "location": location
        },
        "overview": overview_content,
        "news": news_content,
        "reviews": reviews_content,
        "role": role_content,
        "interview": interview_content
    }
    # # loading dummy pickled for testing purposes. 
    # import pickle
    # with open("company_insights_raw_content.pkl", "rb") as f:
    #     raw_content = pickle.load(f)
    
    return company_insights_generator.structure_company_insights(str(raw_content))

async def get_cached_insights(company_name: str, user_role: Optional[str] = None, location: Optional[str] = None):
    """
    **Retrieve cached company insights from MongoDB if they exist.**\n
    \n
    **Parameters:**\n
        - **company_name**: Name of the company\n
        - **user_role**: Optional role to get specific insights for\n
        - **location**: Optional location for regional insights\n
    \n
    **Returns:**\n
        Optional[dict]: Cached insights data if found, None otherwise\n
        {\n
            **"overview"**: dict,            # General company overview\n
            **"news"**: str,                 # Recent news articles\n
            **"reviews"**: dict,             # Company reviews and ratings\n
            **"role_info"**: dict,           # Role-specific information\n
            **"interview_info"**: dict       # Interview-related information\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (500)**: If database operation fails\n
    """
    try:
        # Use case-insensitive regex for all fields
        cache_query = {
            "user_query.company_name": {"$regex": f"^{re.escape(company_name)}$", "$options": "i"},
            "user_query.user_role": {"$regex": f"^{re.escape(user_role if user_role else 'Unknown')}$", "$options": "i"},
            "user_query.location": {"$regex": f"^{re.escape(location if location else 'Unknown')}$", "$options": "i"}
        }
        
        logger.info(f"Cache query: {cache_query}")
        cached_insights = mongodb.company_insights.find_one(cache_query)
        logger.info(f"Found document: {cached_insights is not None}")
        
        if cached_insights:
            logger.info("Found cached insights, returning from cache")
            # Convert MongoDB document to JSON-serializable dict
            return json.loads(json_util.dumps(cached_insights))
            
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
    """
    **Retrieve or generate company insights with optional caching.**\n
    \n
    **Parameters:**\n
        - **company_name**: Name of the company to get insights for\n
        - **user_role**: Optional role to get specific insights for\n
        - **location**: Optional location for regional insights\n
    \n
    **Returns:**\n
        CompanyInsights object containing:\n
        {\n
            **"overview"**: dict,            # General company overview\n
            **"news"**: str,                 # Recent news articles\n
            **"reviews"**: dict,             # Company reviews and ratings\n
            **"role_info"**: dict,           # Role-specific information\n
            **"interview_info"**: dict       # Interview-related information\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (404)**: If company information cannot be found\n
        - **HTTPException (500)**: If insights generation fails\n
    """
    try:
        # Check cache first
        cached_result = await get_cached_insights(company_name, user_role, location)
        if cached_result:
            return cached_result

        # If not in cache, generate new insights
        logger.info("No cache found, generating new insights")
        insights_data = await get_company_insights_(company_name, user_role, location)
        
        # Cache the results - normalize all fields when storing
        insights_dict = insights_data.dict()
        insights_dict["createdAt"] = datetime.utcnow()
        
        # Normalize all user query fields
        insights_dict["user_query"]["company_name"] = company_name.title()
        insights_dict["user_query"]["user_role"] = (user_role.title() if user_role else "Unknown")
        insights_dict["user_query"]["location"] = (location.title() if location else "Unknown")
        
        # Insert into MongoDB
        mongodb.company_insights.insert_one(insights_dict)
        logger.info("Cached new insights")
        
        return insights_data
        
    except Exception as e:
        logger.error(f"Error getting company overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company overview: {str(e)}")