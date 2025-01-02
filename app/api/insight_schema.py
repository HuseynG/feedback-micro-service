from pydantic import BaseModel, Field
from typing import List, Optional
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
    growth_areas: List[str] = Field(description="Growth area of the company")
    challenges: List[str] = Field(description="Challenges of the company")
    opportunities: List[str] = Field(description="Opportunities of the company")
    industry_trends: List[str] = Field(description="Industry trends of the company")

class CompanyNews(BaseModel):
    title: str = Field(description="Title of the news article")
    post_date: datetime = Field(description="Publication date of the news")
    url: str = Field(description="URL to the full news article")

class CompanyReview(BaseModel):
    review: str = Field(description="Content of the review")
    source: str = Field(description="Source of the review")
    source_url: str = Field(description="URL to the original review")
    rating: float = Field(description="Rating given in the review", ge=0, le=5)

class Salary(BaseModel):
    range: Optional[str] = Field(None, description="Salary range")
    currency: Optional[str] = Field(None, description="Salary currency")

class Benefits(BaseModel):
    perks: Optional[List[str]] = Field(None, description="Company perks")
    work_life_balance: Optional[str] = Field(None, description="Work-life balance description")

class Culture(BaseModel):
    values: Optional[List[str]] = Field(None, description="Company values")
    work_style: Optional[str] = Field(None, description="Work style description")
    team_dynamics: Optional[str] = Field(None, description="Team dynamics description")

class CareerGrowth(BaseModel):
    promotion_path: Optional[List[str]] = Field(None, description="Career promotion paths")
    learning_opportunities: Optional[List[str]] = Field(None, description="Learning opportunities")
    mentorship_programs: Optional[str] = Field(None, description="Mentorship programs description")

class WorkEnvironment(BaseModel):
    office_type: Optional[str] = Field(None, description="Type of office environment")
    remote_policy: Optional[str] = Field(None, description="Remote work policy")
    equipment_provided: Optional[List[str]] = Field(None, description="Equipment and tools provided")

class JobRole(BaseModel):
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    responsibilities: List[str] = Field(..., description="Job responsibilities")
    required_skills: List[str] = Field(..., description="Required skills for the job")
    preferred_qualifications: Optional[List[str]] = Field(None, description="Preferred qualifications")
    experience_level: Optional[str] = Field(None, description="Required experience level")

class CompanyRole(BaseModel):
    salary: Salary = Field(..., description="Salary information")
    benefits: Benefits = Field(..., description="Benefits information")
    culture: Culture = Field(..., description="Culture information")
    career_growth: CareerGrowth = Field(..., description="Career growth information")
    work_environment: WorkEnvironment = Field(..., description="Work environment information")
    job_role: JobRole = Field(..., description="Job role information")

class CompanyNewsList(BaseModel):
    news: List[CompanyNews] = Field(description="List of company news articles")

class CompanyReviewList(BaseModel):
    reviews: List[CompanyReview] = Field(description="List of company reviews")

class CompanyInsights(BaseModel):
    overview: CompanyOverview = Field(description="Company overview")
    company_role: CompanyRole = Field(description="Company role")
    news: CompanyNewsList = Field(description="List of company news articles")
    reviews: CompanyReviewList = Field(description="List of company reviews")
