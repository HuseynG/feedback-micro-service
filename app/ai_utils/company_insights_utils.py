from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from api.insight_schema import CompanyInsights, CompanyOverview, CompanyNewsList, CompanyReviewList, CompanyRole, Salary, Benefits, Culture, CareerGrowth, WorkEnvironment, JobRole

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import json

load_dotenv()

class CompanyInsightsGenerator:
    def __init__(self):
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_openai_base_endpoint = os.getenv('AZURE_OPENAI_BASE_API_ENDPOINT')
        azure_openai_api_version = os.getenv('AZURE_OPENAI_API_VERSION')

        self.model = {
            'default_model': '4o-mini',
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

    def structure_company_insights(self, AI_output: str) -> CompanyInsights:
        """
        Takes raw agent output and structures it according to CompanyInsights schema
        using LLM to ensure proper formatting
        """
        system_prompt = """You are a helpful assistant that structures company information.
        Given raw text about a company, extract and structure the information according to the following schema:
        {
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
            "company_role": {
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
            }
        }

        Return the information in valid JSON format that matches this schema exactly.
        If any field is not found in the input, provide a reasonable placeholder or 'Unknown'.
        For news and reviews, if no data is available, return empty lists."""

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
                overview=CompanyOverview(
                    company_name="Unknown",
                    website_url="Unknown",
                    values=["Unknown"],
                    vision="Information not available",
                    size="Unknown",
                    location="Unknown",
                    mission="Information not available",
                    ceo="Unknown",
                    company_type="Unknown",
                    business_nature="Unknown",
                    history="Information not available",
                    growth_area=["Unknown"],
                    challenges=["Unknown"],
                    opportunities=["Unknown"],
                    industry_trends=["Unknown"]
                ),
                news=CompanyNewsList(
                    news=[]
                ),
                reviews=CompanyReviewList(
                    reviews=[]
                ),
                company_role=CompanyRole(
                    salary=Salary(
                        range=None,
                        currency=None
                    ),
                    benefits=Benefits(
                        perks=None,
                        work_life_balance=None
                    ),
                    culture=Culture(
                        values=None,
                        work_style=None,
                        team_dynamics=None
                    ),
                    career_growth=CareerGrowth(
                        promotion_path=None,
                        learning_opportunities=None,
                        mentorship_programs=None
                    ),
                    work_environment=WorkEnvironment(
                        office_type=None,
                        remote_policy=None,
                        equipment_provided=None
                    ),
                    job_role=JobRole(
                        title="Unknown",
                        description="Information not available",
                        responsibilities=["Information not available"],
                        required_skills=["Information not available"],
                        preferred_qualifications=None,
                        experience_level=None
                    )
                )
            )

    async def generate_company_overview(self, company_name: str):

        client = genai.Client()
        model_id = "gemini-2.0-flash-exp"

        google_search_tool = Tool(
            google_search = GoogleSearch()
        )

        response = client.models.generate_content(
            model=model_id,
            contents=f"""
    {company_name}  Company Information,
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
                            Industry Trends""",
            config=GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
            )
        )

        text = ""
        for each in response.candidates[0].content.parts:
            text += each.text + "\n"
        
        return text
    
    async def generate_company_role(self, company_name: str, user_role: str, location: str):
        client = genai.Client()
        model_id = "gemini-2.0-flash-exp"

        google_search_tool = Tool(
            google_search = GoogleSearch()
        )

        response = client.models.generate_content(
            model=model_id,
            contents=f"""Based on the following information, 
            company name: {company_name}
            role: {user_role}
            location: {location}
            
            Please provide information about:
            Salary (range and currency), 
            Benefits (perks, work-life balance, etc), 
            Culture (values, work style, team dynamics, etc), 
            Career Growth (growth opportunities, career progression, etc), 
            Work Environment (work hours, work from home, etc), 
            Job Role (title, responsibilities, skills required, preferred Qualifications, experience level, etc.).""",
            config=GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
            )
        )

        text = ""
        for each in response.candidates[0].content.parts:
            text += each.text + "\n"
        
        return text