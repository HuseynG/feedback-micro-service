from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from api.insight_schema import CompanyInsights, CompanyOverview, CompanyNewsList, CompanyReviewList, RoleInsight, Salary, Benefits, Culture, CareerGrowth, WorkEnvironment, JobRole, InterviewInsights, CommonQuestions, InterviewProcess, PreparationGuide

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import json
import asyncio

load_dotenv()

class CompanyInsightsGenerator:
    def __init__(self):
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_openai_base_endpoint = os.getenv('AZURE_OPENAI_BASE_API_ENDPOINT')
        azure_openai_api_version = os.getenv('AZURE_OPENAI_API_VERSION')

        self.model = {
            'default_model': '4o-mini',
            'overview_model': 'gemini-2.0-flash-exp',
            'role_model': 'gemini-2.0-flash-exp',
            'interview_model': 'gemini-2.0-flash-exp'
        }

        self.llm = AzureChatOpenAI(
            openai_api_key=api_key,
            azure_endpoint=azure_openai_base_endpoint,
            openai_api_type="azure",
            openai_api_version=azure_openai_api_version,
            deployment_name=self.model["default_model"],
            temperature=0,
            seed=123
        )

        self.client = genai.Client()
        self.google_search_tool = Tool(
            google_search = GoogleSearch()
        )

    async def _generate_content(self, prompt: str, model_name: str):
        """Helper method to make async API calls to Gemini"""
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model[model_name],
            contents=prompt,
            config=GenerateContentConfig(
                tools=[self.google_search_tool],
                response_modalities=["TEXT"],
            )
        )
        
        text = ""
        for part in response.candidates[0].content.parts:
            text += part.text + "\n"
        return text

    async def generate_company_overview(self, company_name: str):
        prompt = f"""{company_name}  Company Information,
                            Offical Website Link 
                            Company Values, 
                            Company Vision, 
                            Company Mission,
                            Company Size,
                            Company Location,
                            Company CEO,
                            Company Type,
                            Company Business Nature,
                            Company History,
                            Company About Us.
                            Company Outlook such as growth area, challenges, opportunities,
                            Industry Trends"""
        return await self._generate_content(prompt, 'overview_model')

    async def generate_company_role(self, company_name: str, user_role: str, location: str):
        prompt = f"""Based on the following information, 
            company name: {company_name}
            role: {user_role}
            location: {location}
            
            Please provide information about:
            Salary (range and currency), 
            Benefits (perks, work-life balance, etc), 
            Culture (values, work style, team dynamics, etc), 
            Career Growth (growth opportunities, career progression, etc), 
            Work Environment (work hours, work from home, etc), 
            Job Role (title, responsibilities, skills required, preferred Qualifications, experience level, etc.)."""
        return await self._generate_content(prompt, 'role_model')

    async def generate_company_interview(self, company_name: str, user_role: str, location: str):
        prompt = f"""Based on the following information, 
            company name: {company_name}
            role: {user_role}
            location: {location}
            
            Please provide comprehensive interview information organized in the following sections:

            1. Common Interview Questions:
            - Technical interview questions typically asked
            - Behavioral interview questions commonly used
            - Role-specific questions for this position

            2. Interview Process:
            - All stages of the interview process
            - Typical duration of the entire process
            - Tips and advice for candidates

            3. Preparation Guide:
            - Technical preparation recommendations
            - Cultural preparation tips
            - Suggested resources for interview preparation (books, websites, courses)

            Please provide detailed, specific information based on real experiences and data.
            Focus on actual practices at {company_name} rather than generic advice."""
        return await self._generate_content(prompt, 'interview_model')

    def structure_company_insights(self, AI_output: str) -> CompanyInsights:
        """
        Takes raw agent output and structures it according to CompanyInsights schema
        using LLM to ensure proper formatting
        """
        system_prompt = """You are a helpful assistant that structures company information.
        Given raw text about a company, extract and structure the information according to the following schema:
        {
            "user_query": {
                "company_name": str,
                "role": str,
                "location": str
            },
            "overview": {
                "company_name": str,
                "website_url": str,
                "values": list of keywords which are str,
                "vision": str,
                "size": str,
                "location": str,
                "mission": str,
                "ceo": str,
                "company_type": str,
                "business_nature": str,
                "history": str, 
                "growth_areas": list of keywords which are str,
                "challenges": list of keywords which are str,
                "opportunities": list of keywords which are str,
                "industry_trends": list of keywords which are str,
            },
            "news": {
                "news": [
                    {
                        "title": str,
                        "post_date": str,
                        "url": str
                    }
                ]
            },
            "reviews": {
                "reviews": [
                    {
                        "review": str,
                        "source": str,
                        "source_url": str,
                        "rating": float
                    }
                ]
            },
            "role_insight": {
                "salary": {
                    "range": str,
                    "currency": str
                },
                "benefits": {
                    "perks": list[str],
                    "work_life_balance": str
                },
                "culture": {
                    "values": list[str],
                    "work_style": str,
                    "team_dynamics": str
                },
                "career_growth": {
                    "promotion_path": list[str],
                    "learning_opportunities": list[str],
                    "mentorship_programs": str
                },
                "work_environment": {
                    "office_type": str,
                    "remote_policy": str,
                    "equipment_provided": list[str]
                },
                "job_role": {
                    "title": str,
                    "description": str,
                    "responsibilities": list[str],
                    "required_skills": list[str],
                    "preferred_qualifications": list[str],
                    "experience_level": str
                }
            },
            "interview_insights": {
                "common_questions": {
                    "technical": list[str],
                    "behavioral": list[str],
                    "role_specific": list[str]
                },
                "interview_process": {
                    "stages": list[str],
                    "duration": str,
                    "tips": list[str]
                },
                "preparation_guide": {
                    "technical_prep": list[str],
                    "cultural_prep": list[str],
                    "suggested_resources": list[str]
                }
            }
        }

        Return the information in valid JSON format that matches this schema exactly.
        If any field is not found in the input, provide a reasonable placeholder or 'Unknown'.
        For news, reviews, and interview questions, if no data is available, return empty lists."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please structure this company information and provide in valid JSON format:\n{AI_output}")
        ]


        # Convert the structured string response to CompanyOverview model
        try:
            structured_company_overview_model = self.llm.with_structured_output(CompanyInsights)
            response = structured_company_overview_model.invoke(messages)
            response_json = json.loads(response.model_dump_json())
            return CompanyInsights(**response_json)
        except Exception as e:
            # Fallback with basic information if structuring fails
            return CompanyInsights(
                user_query={
                    "company_name": None,
                    "role": None,
                    "location": None
                },
                overview=CompanyOverview(
                    company_name=None,
                    website_url=None,
                    values=[],
                    vision=None,
                    size=None,
                    location=None,
                    mission=None,
                    ceo=None,
                    company_type=None,
                    business_nature=None,
                    history=None,
                    growth_areas=[],
                    challenges=[],
                    opportunities=[],
                    industry_trends=[]
                ),
                news=CompanyNewsList(
                    news=[]
                ),
                reviews=CompanyReviewList(
                    reviews=[]
                ),
                role_insight=RoleInsight(
                    salary=Salary(
                        range=None,
                        currency=None
                    ),
                    benefits=Benefits(
                        perks=[],
                        work_life_balance=None
                    ),
                    culture=Culture(
                        values=[],
                        work_style=None,
                        team_dynamics=None
                    ),
                    career_growth=CareerGrowth(
                        promotion_path=[],
                        learning_opportunities=[],
                        mentorship_programs=None
                    ),
                    work_environment=WorkEnvironment(
                        office_type=None,
                        remote_policy=None,
                        equipment_provided=[]
                    ),
                    job_role=JobRole(
                        title=None,
                        description=None,
                        responsibilities=[],
                        required_skills=[],
                        preferred_qualifications=[],
                        experience_level=None
                    )
                ),
                interview_insights=InterviewInsights(
                    common_questions=CommonQuestions(
                        technical=[],
                        behavioral=[],
                        role_specific=[]
                    ),
                    interview_process=InterviewProcess(
                        stages=[],
                        duration=None,
                        tips=[]
                    ),
                    preparation_guide=PreparationGuide(
                        technical_prep=[],
                        cultural_prep=[],
                        suggested_resources=[]
                    )
                )
            )