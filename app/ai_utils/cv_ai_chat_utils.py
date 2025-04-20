from ai_utils.cv_schema import CV, ATSJobRequirement, CVAnalysisResult, CVAnalysisStats
from ai_utils.prompt_templates import CV_EXTRACTION_PROMPT, CV_FEEDBACK_ANALYSIS_PROMPT, JOB_MATCH_PROMPT

import os
import base64
import json
from pdf2image import convert_from_path
from typing import List, Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Load API keys from environment variables
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_BASE_API_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')

class DocumentProcessor:
    def __init__(self):
        
        self.model = json.loads(os.getenv('MODEL_CONFIG'))

        self.llm = AzureChatOpenAI(
            openai_api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            openai_api_type="azure",
            openai_api_version=AZURE_OPENAI_API_VERSION,
            deployment_name=self.model["default_model"],
            temperature=0,
            seed=123
        )
    
    async def read_cv(self, pdf_path: str, system_prompt: str, output_format: BaseModel) -> Dict[str, Any]:
        """
        Function 1: Extract CV content and return structured data
        """
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            # Create message content
            message_content = [
                {"type": "text", "text": system_prompt}
            ]
            
            # Process images
            for i, image in enumerate(images):
                import io
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
                
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
                print(f"Processed image {i+1}/{len(images)}")

            # Create message with all images
            message = HumanMessage(content=message_content)
            
            # Get response with structured output
            structured_model = self.llm.with_structured_output(output_format)
            response = await structured_model.ainvoke([
                SystemMessage(content=system_prompt),
                message
            ])
            
            return response
            
        except Exception as e:
            raise Exception(f"Error extracting CV content: {str(e)}")

    async def extract_cv_content(self, pdf_path: str) -> CV:
        return await self.read_cv(pdf_path, CV_EXTRACTION_PROMPT, CV)
    
    
    
    
    async def analyze_cv(self, pdf_path: str) -> CVAnalysisStats:
        """
        Function 2: Analyze CV and generate detailed statistics and insights
        
        Args:
            pdf_path (str): Path to the CV PDF file
            
        Returns:
            CVAnalysisStats: Comprehensive analysis of the CV
        """
        try:
            # First extract CV content
            return await self.read_cv(pdf_path, CV_FEEDBACK_ANALYSIS_PROMPT, CVAnalysisStats)
            
        except Exception as e:
            raise Exception(f"Error analyzing CV: {str(e)}")

    async def match_cv_to_job(self, cv: CV, job_req: ATSJobRequirement) -> CVAnalysisResult:
        """
        Function 3: Compare CV against job description
        """
        try:
            # Create job matching message
            message = HumanMessage(content=f"{JOB_MATCH_PROMPT}\n\nCV Content: {json.dumps(cv.model_dump(mode='json'))}\n\nJob Requirements: {json.dumps(job_req.model_dump(mode='json'))}")
            
            # Get structured analysis
            structured_model = self.llm.with_structured_output(CVAnalysisResult)
            response = await structured_model.ainvoke([
                SystemMessage(content=JOB_MATCH_PROMPT),
                message
            ])
            
            return response
            
        except Exception as e:
            raise Exception(f"Error matching CV to job: {str(e)}")



# Example usage
async def main():
    processor = DocumentProcessor()
    pdf_path = "HG_CV.pdf"
    
    try:
        # # Step 1: Extract CV content
        cv_content = await processor.extract_cv_content(pdf_path)
        print("\nStep 1: CV Content Extracted")
        print("="*50)
        print(json.dumps(cv_content.model_dump(mode='json'), indent=2))
        


        # Step 2: Analyze CV
        cv_analysis = await processor.analyze_cv(pdf_path)
        print("\nStep 2: CV Analysis")
        print("="*50)
        print(json.dumps(cv_analysis.model_dump(mode='json'), indent=2))


        
        # Step 3: Match CV to job (example job requirement)
        job_req = ATSJobRequirement(
            job_title="Senior Software Engineer",
            job_description="Looking for an experienced software engineer...",
            required_skills=["Python", "AWS", "Machine Learning"],
            optional_skills=["Docker", "Kubernetes"]
        )
        
        cv_job_match = await processor.match_cv_to_job(cv_content, job_req)
        print("\nStep 3: CV-Job Match Analysis")
        print("="*50)
        print(json.dumps(cv_job_match.model_dump(mode='json'), indent=2))
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    import asyncio
    import io
    asyncio.run(main())