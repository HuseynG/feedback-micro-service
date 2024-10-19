# app/db/schemas.py
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, info) -> 'PyObjectId':
        if not ObjectId.is_valid(value):
            raise ValueError(f'Invalid ObjectId: {value}')
        return cls(value)  # Return PyObjectId instance

    @classmethod
    def __get_pydantic_json_schema__(cls) -> JsonSchemaValue:
        return {"type": "string", "pattern": "^[a-fA-F0-9]{24}$"}

class QuestionBody(BaseModel):
    question: str = Field(..., description="The question to provide feedback for")
    answer: str = Field(..., description="The answer to the question by user")

    def get_combined_Q_info(self) -> str:
        parts = []
        if self.question:
            parts.append(f"Question: {self.question}")
        if self.answer:
            parts.append(f"User Answer: {self.answer}")

        return " | ".join(parts) if parts else "No Question Information Provided."

class ProfileData(BaseModel):
    cv: Optional[str] = None
    cover_letter: Optional[str] = None

class InterviewSummary(BaseModel):
    job_title: str
    job_description: Optional[str] = None
    question_type: str
    role_level: str
    interview_id: str

class QA_Feedback_Model_Content(BaseModel):
    rating: float
    feedback: str

class QA_Feedback_Model(BaseModel):
    content: Optional[QA_Feedback_Model_Content] = None
    coherence: Optional[QA_Feedback_Model_Content] = None
    confidence: Optional[QA_Feedback_Model_Content] = None
    relevance: Optional[QA_Feedback_Model_Content] = None
    professionalism: Optional[QA_Feedback_Model_Content] = None
    appropriateness: Optional[QA_Feedback_Model_Content] = None
    overal_summary: Optional[QA_Feedback_Model_Content] = None

class FollowupQA(BaseModel):
    question: str
    original_user_answer: Optional[str] = None
    ai_modified_user_answer: Optional[str] = None
    ideal_answer: Optional[str] = None
    ai_feedback: Optional[QA_Feedback_Model] = None

class QA(BaseModel):
    question: str
    original_user_answer: Optional[str] = None
    ai_modified_user_answer: Optional[str] = None
    ideal_answer: Optional[str] = None
    ai_feedback: Optional[QA_Feedback_Model] = None
    followup_qas: Optional[List[FollowupQA]] = Field(default_factory=list)  # Now this is a list of FollowupQA

class InterviewBase(BaseModel):
    user: str
    job_title: Optional[str] = None  # Optional job title
    job_description: Optional[str] = None  # Optional job description
    question_type: str  # Should be one of the allowed question types
    role_level: str  # Should be one of the allowed role levels
    company_name: Optional[str] = None  # Optional company name
    profile_data: ProfileData  # Profile data containing CV and cover letter
    industry_standard: bool  # True or False
    QAs: Optional[List[QA]] = Field(default_factory=list)  # Initially, this will be an empty list

    # Model-level validator to ensure either job_title or job_description is provided
    @model_validator(mode='before')
    def check_job_title_or_description(cls, values):
        job_title = values.get('job_title')
        job_description = values.get('job_description')

        if not job_title and not job_description:
            raise ValueError('Either "job_title" or "job_description" must be provided.')

        return values

    # Validator for question_type
    @field_validator('question_type', mode='before')
    def validate_question_type(cls, value):
        allowed_question_types = {'behavioral', 'situational', 'technical', 'general'}
        if value in allowed_question_types:
            return value
        raise ValueError(
            f'Invalid value for "question_type": {value}. Must be one of {allowed_question_types}.'
        )

    # Validator for role_level
    @field_validator('role_level', mode='before')
    def validate_role_level(cls, value):
        allowed_role_levels = {
            'internship', 'entry_level', 'associate', 'mid_senior_level',
            'senior level', 'director', 'executive'
        }
        if value in allowed_role_levels:
            return value
        raise ValueError(
            f'Invalid value for "role_level": {value}. Must be one of {allowed_role_levels}.'
        )
    def get_combined_job_info(self) -> str:
        """
        Combines the job title and job description into a single string.
        If one of them is missing, it returns the available one.
        If both are present, they are concatenated with a separator.
        """
        parts = []
        if self.job_title:
            parts.append(f"Job Title: {self.job_title}")
        if self.job_description:
            parts.append(f"Job Description: {self.job_description}")
        if self.question_type:
            parts.append(f"Question Type: {self.question_type}")
        if self.role_level:
            parts.append(f"Role Level: {self.role_level}")
        if self.company_name:
            parts.append(f"Company Name: {self.company_name}")
        if self.profile_data.cv:
            parts.append(f"User CV: {self.company_name}")
        if self.profile_data.cover_letter:
            parts.append(f"User Cover Letter: {self.company_name}")
        if self.industry_standard:
            parts.append(f"Industry Standard: Also, consider latest development, technologies, terms and practices, etc.")
        
        return " | ".join(parts) if parts else "No Job Information Provided."

class InterviewCreate(InterviewBase):
    pass

class Interview(InterviewBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')

    class Config:
        populate_by_name = True  # Updated from allow_population_by_field_name
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyObjectId: str}  # Added PyObjectId
