from fastapi import APIRouter
import os
from dotenv import load_dotenv
import logging
from typing import Optional, List
from fastapi import HTTPException
from datetime import datetime
from .insight_schema import CompanyOverview, CompanyNewsList, CompanyReviewList, CompanyNews, CompanyReview

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
    """Get company overview information"""
    # Dummy data for demonstration
    return CompanyOverview(
        company_name="Example Tech Corp",
        website_url="https://example.com",
        values=["Innovation", "Integrity", "Customer Focus"],
        vision="To revolutionize technology for a better tomorrow",
        size="1000-5000 employees",
        location="San Francisco, CA",
        mission="To provide cutting-edge solutions that empower businesses",
        ceo="John Smith",
        company_type="Corporation",
        business_nature="Technology and Software Development",
        history="Founded in 2010, Example Tech Corp has grown from a small startup to a leading technology provider..."
    )

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