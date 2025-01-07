from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CompanyOverview(BaseModel):
    company_name: Optional[str] = Field(None, description="Name of the company")
    website_url: Optional[str] = Field(None, description="URL of the company website")
    values: List[str] = Field(default_factory=list, description="Company core values")
    vision: Optional[str] = Field(None, description="Company vision statement")
    size: Optional[str] = Field(None, description="Company size/number of employees")
    location: Optional[str] = Field(None, description="Company headquarters location")
    mission: Optional[str] = Field(None, description="Company mission statement")
    ceo: Optional[str] = Field(None, description="CEO or owner of the company")
    company_type: Optional[str] = Field(None, description="Type of company (e.g., LLC, Corporation)")
    business_nature: Optional[str] = Field(None, description="Nature of business/industry")
    history: Optional[str] = Field(None, description="Brief company history")
    growth_areas: List[str] = Field(default_factory=list, description="Growth area of the company")
    challenges: List[str] = Field(default_factory=list, description="Challenges of the company")
    opportunities: List[str] = Field(default_factory=list, description="Opportunities of the company")
    industry_trends: List[str] = Field(default_factory=list, description="Industry trends of the company")

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
    perks: List[str] = Field(default_factory=list, description="Company perks")
    work_life_balance: Optional[str] = Field(None, description="Work-life balance description")

class Culture(BaseModel):
    values: List[str] = Field(default_factory=list, description="Company values")
    work_style: Optional[str] = Field(None, description="Work style description")
    team_dynamics: Optional[str] = Field(None, description="Team dynamics description")

class CareerGrowth(BaseModel):
    promotion_path: List[str] = Field(default_factory=list, description="Career promotion paths")
    learning_opportunities: List[str] = Field(default_factory=list, description="Learning opportunities")
    mentorship_programs: Optional[str] = Field(None, description="Mentorship programs description")

class WorkEnvironment(BaseModel):
    office_type: Optional[str] = Field(None, description="Type of office environment")
    remote_policy: Optional[str] = Field(None, description="Remote work policy")
    equipment_provided: List[str] = Field(default_factory=list, description="Equipment and tools provided")

class JobRole(BaseModel):
    title: Optional[str] = Field(None, description="Job title")
    description: Optional[str] = Field(None, description="Job description")
    responsibilities: List[str] = Field(default_factory=list, description="Job responsibilities")
    required_skills: List[str] = Field(default_factory=list, description="Required skills for the job")
    preferred_qualifications: List[str] = Field(default_factory=list, description="Preferred qualifications")
    experience_level: Optional[str] = Field(None, description="Required experience level")

class RoleInsight(BaseModel):
    salary: Salary = Field(default_factory=Salary, description="Salary information")
    benefits: Benefits = Field(default_factory=Benefits, description="Benefits information")
    culture: Culture = Field(default_factory=Culture, description="Culture information")
    career_growth: CareerGrowth = Field(default_factory=CareerGrowth, description="Career growth information")
    work_environment: WorkEnvironment = Field(default_factory=WorkEnvironment, description="Work environment information")
    job_role: JobRole = Field(default_factory=JobRole, description="Job role information")

class CompanyNewsList(BaseModel):
    news: List[CompanyNews] = Field(default_factory=list, description="List of company news articles")

class CompanyReviewList(BaseModel):
    reviews: List[CompanyReview] = Field(default_factory=list, description="List of company reviews")

class InterviewProcess(BaseModel):
    stages: List[str] = Field(default_factory=list, description="Interview process stages")
    duration: Optional[str] = Field(None, description="Typical interview process duration")
    tips: List[str] = Field(default_factory=list, description="Interview tips and advice")

class PreparationGuide(BaseModel):
    technical_prep: List[str] = Field(default_factory=list, description="Technical preparation tips")
    cultural_prep: List[str] = Field(default_factory=list, description="Cultural preparation tips")
    suggested_resources: List[str] = Field(default_factory=list, description="Suggested preparation resources")

class CommonQuestions(BaseModel):
    technical: List[str] = Field(default_factory=list, description="Common technical interview questions")
    behavioral: List[str] = Field(default_factory=list, description="Common behavioral interview questions")
    role_specific: List[str] = Field(default_factory=list, description="Role-specific interview questions")

class InterviewInsights(BaseModel):
    common_questions: CommonQuestions = Field(default_factory=CommonQuestions, description="Common interview questions")
    interview_process: InterviewProcess = Field(default_factory=InterviewProcess, description="Interview process")
    preparation_guide: PreparationGuide = Field(default_factory=PreparationGuide, description="Preparation guide")

class CompanyInsights(BaseModel):
    overview: CompanyOverview = Field(default_factory=CompanyOverview, description="Company overview")
    role_insight: RoleInsight = Field(default_factory=RoleInsight, description="Company role")
    news: CompanyNewsList = Field(default_factory=CompanyNewsList, description="List of company news articles")
    reviews: CompanyReviewList = Field(default_factory=CompanyReviewList, description="List of company reviews")
    interview_insights: InterviewInsights = Field(default_factory=InterviewInsights, description="Interview insights")