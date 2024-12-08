from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from api.insight_schema import CompanyOverview

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

    async def structure_company_overview(self, agent_output: str) -> CompanyOverview:
        """
        Takes raw agent output and structures it according to CompanyOverview schema
        using LLM to ensure proper formatting
        """
        system_prompt = """You are a helpful assistant that structures company information.
        Given raw text about a company, extract and structure the information according to the following schema:
        - company_name: str
        - website_url: str
        - values: list of strings
        - vision: str
        - size: str
        - location: str
        - mission: str
        - ceo: str
        - company_type: str
        - business_nature: str
        - history: str

        Return the information in valid JSON format that matches this schema exactly.
        If any field is not found in the input, provide a reasonable placeholder or 'Unknown'."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please structure this company information:\n{agent_output}")
        ]

        response = await self.llm.ainvoke(messages)
        structured_data = response.content

        # Convert the structured string response to CompanyOverview model
        try:
            import json
            data = json.loads(structured_data)
            return CompanyOverview(**data)
        except Exception as e:
            # Fallback with basic information if structuring fails
            return CompanyOverview(
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
            )
