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

class ProfileData(BaseModel):
    cv: str
    cover_letter: str

class QA(BaseModel):
    question: str
    user_answer: Optional[str] = None
    ideal_answer: Optional[str] = None

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

class InterviewCreate(InterviewBase):
    pass

class Interview(InterviewBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias='_id')

    class Config:
        populate_by_name = True  # Updated from allow_population_by_field_name
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyObjectId: str}  # Added PyObjectId
