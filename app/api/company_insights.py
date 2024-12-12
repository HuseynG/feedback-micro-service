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
import pickle
from ai_utils.agent_utils.tools.ai_web_reader import read_webpages
from ai_utils.chatbot_utils import AI_Generator

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ai_generator = AI_Generator()

router = APIRouter(
    prefix="/company_insights",
    tags=["company_insights"],
    responses={404: {"description": "Not found"}},
)

@router.get("/overview/{company_name}")
async def get_company_overview(company_name: str):
    """Get company overview information using AI agent"""
    try:
        # url = "https://linkedin-data-api.p.rapidapi.com/get-company-insights"

        # querystring = {"username":company_name}

        # headers = {
        #     "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        #     "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com"
        # }

        # response = requests.get(url, headers=headers, params=querystring)

        # Load the response from the file
        with open("overview_response.pkl", "rb") as file:
            response = pickle.load(file)

        return response.json()
        
    except Exception as e:
        logger.error(f"Error getting company overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting company overview: {str(e)}")

@router.get("/news/{company_name}", response_model=CompanyNewsList)
async def get_company_news(company_name: str):
    """Get company news articles"""

    news_url = f"https://www.bing.com/news/search?q={company_name}"
        # Fetch news content
    results = await read_webpages([news_url])
    if not results[0].success:
        raise HTTPException(status_code=500, detail="Failed to fetch news")
    
    news_content = "".join(r.content for r in results)
    
    content_organiser_response = ai_generator.organise_with_schema(news_content, CompanyNewsList)

    logger.debug(f"Getting company news for {content_organiser_response}")
    
    # Dummy data for demonstration
    return content_organiser_response

@router.get("/reviews/{company_name}",)
async def get_company_reviews(company_name: str):
    """Get company reviews from various sources"""
    
    # url = "https://real-time-glassdoor-data.p.rapidapi.com/company-search"

    # querystring = {"query":company_name,"limit":"10"}

    # headers = {
    #     "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    #     "x-rapidapi-host": "real-time-glassdoor-data.p.rapidapi.com"
    # }

    # response = requests.get(url, headers=headers, params=querystring)

    # company_id = response.json()['data'][0]['company_id']
    
    # url = "https://real-time-glassdoor-data.p.rapidapi.com/company-reviews"

    # querystring = {"company_id":company_id,"page":"1","sort":"POPULAR","language":"en","only_current_employees":"false","extended_rating_data":"false"}

    # headers = {
    #     "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    #     "x-rapidapi-host": "real-time-glassdoor-data.p.rapidapi.com"
    # }

    # response = requests.get(url, headers=headers, params=querystring)

    # # Save the response to a file
    # with open("reviews_response.pkl", "wb") as file:
    #     pickle.dump(response, file)

    # Load the response from the file
    with open("reviews_response.pkl", "rb") as file:
        response = pickle.load(file)

    return response.json()