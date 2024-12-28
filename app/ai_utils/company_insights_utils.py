from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from api.insight_schema import CompanyInsights, CompanyOverview, CompanyNewsList, CompanyReviewList

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
                "values": list of strings,
                "vision": str,
                "size": str,
                "location": str,
                "mission": str,
                "ceo": str,
                "company_type": str,
                "business_nature": str,
                "history": str
            },
            "news": {
                "articles": [
                    {
                        "title": str,
                        "date": str,
                        "summary": str,
                        "source": str
                    }
                ]
            },
            "reviews": {
                "reviews": [
                    {
                        "rating": float,
                        "text": str,
                        "date": str,
                        "source": str
                    }
                ]
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
                    history="Information not available"
                ),
                news=CompanyNewsList(
                    articles=[]  # Empty list for news articles
                ),
                reviews=CompanyReviewList(
                    reviews=[]  # Empty list for reviews
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
                            Company About Us.""",
            config=GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
            )
        )

        text = ""
        for each in response.candidates[0].content.parts:
            text += each.text + "\n"
        
        return text