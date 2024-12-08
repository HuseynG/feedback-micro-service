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


# TODO: Company Overview: https://www.bing.com/search?q=ExComS

# TODO: Company Values: Via Agent

# TODO: Company News, Recent News: https://www.bing.com/news/search?q=Apple

# TODO: Company Reviews: Agents