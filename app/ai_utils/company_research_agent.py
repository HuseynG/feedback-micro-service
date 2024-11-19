from typing import Sequence, TypedDict, Dict, List, Optional
from datetime import datetime
import logging
import re
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.tools import TavilySearchResults
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define structured output types
class NewsItem(TypedDict):
    title: str
    summary: str
    date: str
    source: str
    url: str

class JobPosting(TypedDict):
    title: str
    location: str
    description: str
    url: str
    required_skills: List[str]

class CompanyOverview(TypedDict):
    vision: str
    mission: str
    values: List[str]
    recent_news: List[NewsItem]

class CompanyResearchOutput(TypedDict):
    company_name: str
    company_overview: CompanyOverview
    job_postings: Optional[List[JobPosting]]
    company_reviews: Optional[List[Dict]]
    research_metadata: Dict
    timing_report: Dict

class CompanyResearchConfig(BaseModel):
    """Configuration for company research"""
    include_jobs: bool = Field(default=True)
    include_reviews: bool = Field(default=True)
    max_news_items: int = Field(default=10)
    max_jobs: int = Field(default=7)

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    config: CompanyResearchConfig
    user_interests: List[str]
    company_name: str
    structured_output: Optional[CompanyResearchOutput]

# Custom tools with structured output
class CompanyResearchTools:
    def __init__(self, serper_api_key: str, tavily_api_key: str):
        self.tavily_search = TavilySearchResults(
            api_key=tavily_api_key,
            max_results=10,
            search_depth="advanced",
            include_raw_content=True,
            include_images=False
        )
        self.serper = GoogleSerperAPIWrapper(
            serper_api_key=serper_api_key,
            gl="us",
            hl="en",
            type="search"
        )
        self.ddg_search = DuckDuckGoSearchRun()
        self.sources = set()  # Add a set to track sources

    def add_source(self, url: str):
        """Add source URL to tracking"""
        if url and isinstance(url, str) and url.startswith('http'):
            self.sources.add(url)

    def clean_company_name(self, company_name: str) -> tuple:
        """Clean company name and create variations for search"""
        # Remove common legal suffixes
    def search_company_info(self, company_name: str) -> CompanyOverview:
        """Search for company information including vision, mission, and values"""
        # First, try to get the company's official website
        official_site = None
        try:
            site_query = f'"{company_name}" official website company'
            site_results = self.serper.results(site_query)
            if isinstance(site_results, dict) and 'organic' in site_results:
                for result in site_results['organic'][:3]:
                    url = result.get('link', '')
                    if url and not any(x in url for x in ['linkedin', 'facebook', 'twitter', 'instagram']):
                        official_site = url
                        self.add_source(url)
                        break
        except Exception as e:
            logger.error(f"Error finding official website: {str(e)}")

        # Specific queries for different aspects
        queries = [
            # Official sources
            f'"{company_name}" about us company profile site:{official_site}' if official_site else None,
            f'"{company_name}" mission vision values site:{official_site}' if official_site else None,
            # Business directories
            f'"{company_name}" company profile site:bloomberg.com OR site:reuters.com OR site:dnb.com',
            f'"{company_name}" about company site:crunchbase.com OR site:zoominfo.com',
            # General search
            f'"{company_name}" "mission statement" "vision statement"',
            f'"{company_name}" "core values" "company culture"'
        ]

        all_results = []
        for query in queries:
            if not query:
                continue
            try:
                serper_results = self.serper.results(query)
                if isinstance(serper_results, dict):
                    organic_results = serper_results.get('organic', [])
                    for result in organic_results:
                        snippet = result.get('snippet', '')
                        # Only include if it's relevant
                        if (company_name.lower() in snippet.lower() and 
                            any(keyword in snippet.lower() for keyword in 
                                ['mission', 'vision', 'values', 'about us', 'profile'])):
                            all_results.append(snippet)
                            self.add_source(result.get('link'))
            except Exception as e:
                logger.error(f"Error in query '{query}': {str(e)}")

        # Combine and clean results
        combined_text = " ".join(all_results)

        # Extract vision with improved patterns
        vision = ""
        vision_patterns = [
            rf"{company_name}.*?vision\s+is\s+to\s+([\w\s,]+(?:\.|$))",
            r"vision\s+is\s+to\s+([\w\s,]+(?:\.|$))",
            r"vision:\s*([\w\s,]+(?:\.|$))",
            r"vision\s+statement:\s*([\w\s,]+(?:\.|$))"
        ]
        for pattern in vision_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE | re.MULTILINE)
            if match:
                vision = match.group(1).strip()
                if len(vision) > 10:  # Ensure it's meaningful
                    break

        # Extract mission with improved patterns
        mission = ""
        mission_patterns = [
            rf"{company_name}.*?mission\s+is\s+to\s+([\w\s,]+(?:\.|$))",
            r"mission\s+is\s+to\s+([\w\s,]+(?:\.|$))",
            r"mission:\s*([\w\s,]+(?:\.|$))",
            r"mission\s+statement:\s*([\w\s,]+(?:\.|$))"
        ]
        for pattern in mission_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE | re.MULTILINE)
            if match:
                mission = match.group(1).strip()
                if len(mission) > 10:  # Ensure it's meaningful
                    break

        # Extract values with improved context
        values = set()
        common_values = {
            "integrity", "innovation", "excellence", "customer focus",
            "teamwork", "accountability", "quality", "respect",
            "transparency", "sustainability", "diversity", "inclusion"
        }

        # Look for explicit value statements
        value_patterns = [
            r"(?:core\s+)?values\s+(?:include|are|:)\s*((?:[\w\s,]+(?:and|&)?)+)",
            r"(?:our|company)\s+values\s*(?:include|are|:)\s*((?:[\w\s,]+(?:and|&)?)+)"
        ]
        
        for pattern in value_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                value_text = match.group(1)
                value_list = re.split(r'[,.]|\sand\s|\s&\s', value_text)
                for value in value_list:
                    value = value.strip().lower()
                    if len(value) > 3 and not any(word in value for word in ['are', 'our', 'the']):
                        values.add(value.capitalize())

        # Add common values if found in text
        for value in common_values:
            if value.lower() in combined_text.lower():
                values.add(value.capitalize())

        # Ensure we have meaningful values
        final_values = list(values)[:5] if values else ["Not available"]

        return CompanyOverview(
            vision=vision or "Not available",
            mission=mission or "Not available",
            values=final_values,
            recent_news=[]
        )

    def search_company_news(self, company_name: str, max_items: int) -> List[NewsItem]:
        """Search for recent company news"""
        news_items = []
        
        try:
            news_serper = GoogleSerperAPIWrapper(
                serper_api_key=self.serper.serper_api_key,
                gl="us",
                hl="en",
                type="news"
            )
            
            # More specific news queries
            queries = [
                f'"{company_name}" company news',
                f'"{company_name}" press release',
                f'"{company_name}" announcements'
            ]
            
            for query in queries[:2]:
                try:
                    results = news_serper.results(query)
                    
                    if isinstance(results, dict) and 'news' in results:
                        for item in results['news']:
                            # Only include news that mentions the company name
                            if company_name.lower() in (item.get('title', '') + item.get('snippet', '')).lower():
                                title = item.get('title', '').strip()
                                url = item.get('link', '')
                                source = item.get('source', 'News Source')
                                date = item.get('date', 'Recent')
                                snippet = item.get('snippet', '')

                                if len(title) > 10 and url:
                                    news_item = NewsItem(
                                        title=title[:100],
                                        summary=snippet[:200] + "..." if len(snippet) > 200 else snippet,
                                        date=date,
                                        source=source,
                                        url=url
                                    )
                                    
                                    if not any(existing["url"] == news_item["url"] for existing in news_items):
                                        news_items.append(news_item)
                                        self.add_source(url)
                                        
                                        if len(news_items) >= max_items:
                                            break

                except Exception as e:
                    logger.error(f"Error processing query '{query}': {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in search_company_news: {str(e)}")

        return news_items[:max_items]

    def search_job_postings(self, company_name: str, user_interests: List[str], max_jobs: int) -> List[JobPosting]:
        """Search for job postings matching user interests"""
        jobs = []
        
        try:
            for interest in user_interests:
                # More specific job queries
                query = f'"{company_name}" careers jobs hiring {interest} site:linkedin.com OR site:indeed.com OR site:glassdoor.com'
                results = self.serper.results(query)
                
                if isinstance(results, dict) and 'organic' in results:
                    for item in results['organic']:
                        # Only include job postings that mention both company and interest
                        if (company_name.lower() in item.get('snippet', '').lower() and 
                            interest.lower() in item.get('snippet', '').lower()):
                            title = item.get('title', '').split(' - ')[0].strip()
                            url = item.get('link', '')
                            snippet = item.get('snippet', '')

                            if len(title) > 10 and url:
                                # Extract location with better patterns
                                location = "Remote"
                                location_patterns = [
                                    r"location:?\s*([^\.]+)",
                                    r"based in\s*([^\.]+)",
                                    r"position in\s*([^\.]+)",
                                    r"located in\s*([^\.]+)"
                                ]
                                for pattern in location_patterns:
                                    match = re.search(pattern, snippet, re.IGNORECASE)
                                    if match:
                                        location = match.group(1).strip()
                                        break

                                # Extract skills with better context
                                skills = [interest]
                                skill_keywords = [
                                    "python", "java", "c++", "javascript", "sql",
                                    "machine learning", "ai", "data science", "cloud",
                                    "aws", "azure", "agile", "devops"
                                ]
                                for skill in skill_keywords:
                                    if re.search(r'\b' + re.escape(skill) + r'\b', snippet.lower()):
                                        if skill not in skills:
                                            skills.append(skill)

                                jobs.append(JobPosting(
                                    title=title,
                                    location=location,
                                    description=snippet[:200] + "..." if len(snippet) > 200 else snippet,
                                    url=url,
                                    required_skills=skills
                                ))
                                self.add_source(url)
                                
                                if len(jobs) >= max_jobs:
                                    break
                
                if len(jobs) >= max_jobs:
                    break

        except Exception as e:
            logger.error(f"Error in search_job_postings: {str(e)}")

        # Remove duplicates based on URL and relevance
        unique_jobs = []
        seen_urls = set()
        for job in jobs:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                unique_jobs.append(job)

        return unique_jobs[:max_jobs]

    def get_sources(self) -> List[str]:
        """Get all tracked source URLs"""
        return list(self.sources)

    def search_company_reviews(self, company_name: str, max_reviews: int = 5) -> List[Dict]:
        """Search for company reviews from various platforms"""
        reviews = []
        
        try:
            # Create specific queries for reviews
            queries = [
                f"{company_name} company reviews site:glassdoor.com",
                f"{company_name} employee reviews site:indeed.com",
                f"{company_name} workplace reviews site:comparably.com"
            ]
            
            for query in queries:
                try:
                    results = self.serper.results(query)
                    
                    if isinstance(results, dict) and 'organic' in results:
                        for item in results['organic']:
                            snippet = item.get('snippet', '')
                            title = item.get('title', '')
                            url = item.get('link', '')
                            
                            # Skip if it's not a review
                            if not any(word in snippet.lower() for word in ['review', 'rating', 'stars', 'employees']):
                                continue
                            
                            # Extract rating if available
                            rating = None
                            rating_patterns = [
                                r'(\d+\.?\d*)\s*out of\s*5',
                                r'(\d+\.?\d*)\s*stars?',
                                r'(\d+\.?\d*)/5'
                            ]
                            for pattern in rating_patterns:
                                import re
                                match = re.search(pattern, snippet + title)
                                if match:
                                    try:
                                        rating = float(match.group(1))
                                        break
                                    except ValueError:
                                        continue
                            
                            # Extract review date
                            date = "Recent"
                            date_patterns = ["posted", "reviewed", "written", "updated"]
                            for pattern in date_patterns:
                                if pattern in snippet.lower():
                                    date_part = snippet[snippet.lower().find(pattern)-20:].split('.')[0]
                                    date = date_part.strip()
                                    break
                            
                            # Extract source
                            source = "Unknown"
                            if "glassdoor" in url.lower():
                                source = "Glassdoor"
                            elif "indeed" in url.lower():
                                source = "Indeed"
                            elif "comparably" in url.lower():
                                source = "Comparably"
                            
                            review = {
                                "rating": rating,
                                "summary": snippet[:200] + "..." if len(snippet) > 200 else snippet,
                                "date": date,
                                "source": source,
                                "url": url
                            }
                            
                            # Add only if we have meaningful content
                            if len(review["summary"]) > 20 and url:
                                reviews.append(review)
                                self.add_source(url)
                                
                                if len(reviews) >= max_reviews:
                                    break
                
                    if len(reviews) >= max_reviews:
                        break
                    
                except Exception as e:
                    logger.error(f"Error processing review query '{query}': {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in search_company_reviews: {str(e)}")

        # Sort reviews by rating (if available)
        reviews.sort(key=lambda x: x["rating"] if x["rating"] is not None else 0, reverse=True)
        
        return reviews[:max_reviews]

class CompanyResearchAgent:
    def __init__(self, azure_endpoint: str, azure_api_key: str, deployment_name: str,
                 api_version: str, serper_api_key: str, tavily_api_key: str):
        
        # Initialize the LLM
        self.llm = AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            deployment_name=deployment_name,
            api_version=api_version,
            temperature=0
        )
        
        # Initialize tools
        self.research_tools = CompanyResearchTools(serper_api_key, tavily_api_key)
        
        # Create tools with proper argument handling
        self.tools = [
            Tool(
                name="search_company_info",
                description="Search for company information including vision, mission, and values",
                func=lambda x: self.research_tools.search_company_info(company_name=x)
            ),
            StructuredTool.from_function(
                func=self.research_tools.search_company_news,
                name="search_company_news",
                description="Search for recent news about the company",
            ),
            StructuredTool.from_function(
                func=self.research_tools.search_job_postings,
                name="search_job_postings",
                description="Search for job postings from the company matching user interests",
            ),
            StructuredTool.from_function(
                func=self.research_tools.search_company_reviews,
                name="search_company_reviews",
                description="Search for company reviews from various platforms",
            )
        ]

        # Create the agent prompt with fixed formatting
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert company research agent. Your task is to gather comprehensive 
information about companies using the available tools.

Available tools and their usage:
1. search_company_info: 
   Input: company name as string
   Example: "Microsoft Corporation"

2. search_company_news:
   Input: 
   - company_name: string (required)
   - max_items: integer (optional, default=10)

3. search_job_postings:
   Input:
   - company_name: string (required)
   - user_interests: list of strings (optional)
   - max_jobs: integer (optional, default=7)

4. search_company_reviews:
   Input:
   - company_name: string (required)
   - max_reviews: integer (optional, default=5)

Follow these steps:
1. First, get basic company info using search_company_info
2. Then, get news using search_company_news
3. If jobs are requested, use search_job_postings
4. If reviews are requested, use search_company_reviews

Remember to provide all required parameters for each tool."""),
            ("human", "Research this company: {input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create the agent
        self.agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def research_company(self, company_name: str, config: CompanyResearchConfig,
                        user_interests: Optional[List[str]] = None) -> CompanyResearchOutput:
        """Research a company using the agent and return structured information"""
        start_time = datetime.now()
        logger.info(f"Starting research for company: {company_name}")

        try:
            # Prepare the input for the agent
            agent_input = {
                "input": f"""Company: {company_name}
Configuration:
- Include jobs: {config.include_jobs}
- Include reviews: {config.include_reviews}
- Max news items: {config.max_news_items}
- Max jobs: {config.max_jobs}
User interests: {', '.join(user_interests) if user_interests else 'None'}"""
            }

            # Execute the agent
            agent_result = self.agent_executor.invoke(agent_input)
            
            # Process results directly
            company_info = self.research_tools.search_company_info(company_name)
            news_items = self.research_tools.search_company_news(
                company_name=company_name,
                max_items=config.max_news_items
            )
            company_info["recent_news"] = news_items

            job_postings = []
            if config.include_jobs:
                job_postings = self.research_tools.search_job_postings(
                    company_name=company_name,
                    user_interests=user_interests or [],
                    max_jobs=config.max_jobs
                )

            company_reviews = []
            if config.include_reviews:
                company_reviews = self.research_tools.search_company_reviews(
                    company_name=company_name,
                    max_reviews=5
                )

            # Create result
            end_time = datetime.now()
            return CompanyResearchOutput(
                company_name=company_name,
                company_overview=company_info,
                job_postings=job_postings,
                company_reviews=company_reviews,
                research_metadata={
                    "timestamp": datetime.now().isoformat(),
                    "sources": self.research_tools.get_sources(),
                    "agent_thoughts": agent_result.get("intermediate_steps", [])
                },
                timing_report={
                    "Total Execution": f"{(end_time - start_time).total_seconds():.2f} seconds"
                }
            )

        except Exception as e:
            logger.error(f"Error in research_company: {str(e)}", exc_info=True)
            return CompanyResearchOutput(
                company_name=company_name,
                company_overview=CompanyOverview(
                    vision="",
                    mission="",
                    values=[],
                    recent_news=[]
                ),
                job_postings=[],
                company_reviews=[],
                research_metadata={
                    "timestamp": datetime.now().isoformat(),
                    "sources": []
                },
                timing_report={
                    "Total Execution": f"{(datetime.now() - start_time).total_seconds():.2f} seconds"
                }
            ) 