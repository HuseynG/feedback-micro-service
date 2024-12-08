from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class CompanyOverview(BaseModel):
    company_name: str = Field(description="Name of the company")
    website_url: str = Field(description="URL of the company website")
    values: List[str] = Field(description="Company core values")
    vision: str = Field(description="Company vision statement")
    size: str = Field(description="Company size/number of employees")
    location: str = Field(description="Company headquarters location")
    mission: str = Field(description="Company mission statement")
    ceo: str = Field(description="CEO or owner of the company")
    company_type: str = Field(description="Type of company (e.g., LLC, Corporation)")
    business_nature: str = Field(description="Nature of business/industry")
    history: str = Field(description="Brief company history")

class CompanyNews(BaseModel):
    title: str = Field(description="Title of the news article")
    post_date: datetime = Field(description="Publication date of the news")
    url: str = Field(description="URL to the full news article")

class CompanyReview(BaseModel):
    review: str = Field(description="Content of the review")
    source: str = Field(description="Source of the review")
    source_url: str = Field(description="URL to the original review")
    rating: float = Field(description="Rating given in the review", ge=0, le=5)

class CompanyNewsList(BaseModel):
    news: List[CompanyNews] = Field(description="List of company news articles")

class CompanyReviewList(BaseModel):
    reviews: List[CompanyReview] = Field(description="List of company reviews")
