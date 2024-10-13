import os
from dotenv import load_dotenv
load_dotenv()
import json

from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import ai_utils.prompt_templates as prompt_templates

from pydantic import BaseModel, Field
from typing import List, Optional


class QA_Feedback_Model_Content(BaseModel):
    rating: float = Field(None, alias="rating", description="The rating is between 1-10. 1 being lowest and 10 being highest rating") # 1-10
    feedback: str = Field(None, alias="feedback", description="The interview question.") # str

class QA_Feedback_Model(BaseModel):
    content: Optional[QA_Feedback_Model_Content] = Field(None, alias="content", description="Feedback on the content of the user answer.")
    coherence: Optional[QA_Feedback_Model_Content] = Field(None, alias="coherence", description="Feedback on the coherence of the user answer.")
    confidence: Optional[QA_Feedback_Model_Content] = Field(None, alias="confidence", description="Feedback on the confidence of the user based on the answer.")
    relevance: Optional[QA_Feedback_Model_Content] = Field(None, alias='relevance', description="Feedback on the relevance of the user answer.")
    professionalism: Optional[QA_Feedback_Model_Content] = Field(None, alias='professionalism', description="Feedback on the professionalism of the user's answer.")
    appropriateness: Optional[QA_Feedback_Model_Content] = Field(None, alias='appropriateness', description="Feedback on the appropriateness of the user's answer.")
    overal_summary: Optional[QA_Feedback_Model_Content] = Field(None, alias='overal_summary', description="Overall Feedback on the user's answer.")

# AI model response schemas
class QA(BaseModel):
    question: str = Field(..., alias="question", description="The interview question.")
    original_user_answer: Optional[str] = Field(
        None, alias="original_user_answer", description="The answer provided by the user."
    )
    ai_modified_user_answer: Optional[str] = Field(
        None, alias="ai_modified_user_answer", description="The AI-rectified user answer."
    )
    ideal_answer: Optional[str] = Field(
        None, alias="ideal_answer", description="The best possible answer based on the ideal scenario."
    )
    ai_feedback: Optional[QA_Feedback_Model] = Field(
        None, alias="ai_feedback", description="Feedback provided by the AI.")

class InterviewQuestions(BaseModel): 
    qas: List[QA] = Field(
        ..., alias="qas", description="List of question-answer items."
    )

class AI_Generator:
    def __init__(self):

        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_openai_base_endpoint = os.getenv('AZURE_OPENAI_BASE_API_ENDPOINT')
        azure_openai_api_version = os.getenv('AZURE_OPENAI_API_VERSION')

        self.model = {
            'defualt_model':'4o-mini',
        }

        self.question_generator_model = AzureChatOpenAI(
            openai_api_key=api_key,
            azure_endpoint=azure_openai_base_endpoint,
            openai_api_type="azure",
            openai_api_version=azure_openai_api_version,
            deployment_name=self.model["defualt_model"],
            temperature=0,
            seed=123
        )

        self.question_feedback_generator_model = AzureChatOpenAI(
            openai_api_key=api_key,
            azure_endpoint=azure_openai_base_endpoint,
            openai_api_type="azure",
            openai_api_version=azure_openai_api_version,
            deployment_name=self.model["defualt_model"],
            temperature=0,
            seed=123
        )

    def generate_questions(self, text):

        system_prompt = prompt_templates.question_generator_model_system_prompt_template
        user_prompt = prompt_templates.question_generator_model_user_prompt_template

        system_message = SystemMessage(content=system_prompt)
        user_message = HumanMessage(content=user_prompt.format(text=text))

        convo = [system_message, user_message]

        structured_question_generator_model = self.question_generator_model.with_structured_output(InterviewQuestions)
        response = structured_question_generator_model.invoke(convo)
        response_json = json.loads(response.model_dump_json())  # converting to json/dict object type

        return response_json
    
    def generate_q_feedback(self, text):

        system_prompt = prompt_templates.question_feedback_generator_model_system_prompt_template
        user_prompt = prompt_templates.question_feedback_generator_model_user_prompt_template

        system_message = SystemMessage(content=system_prompt)
        user_message = HumanMessage(content=user_prompt.format(text=text))

        convo = [system_message, user_message]

        structured_question_feedback_generator_model = self.question_feedback_generator_model.with_structured_output(QA)
        response = structured_question_feedback_generator_model.invoke(convo)
        response_json = json.loads(response.model_dump_json())  # converting to json/dict object type

        return response_json
