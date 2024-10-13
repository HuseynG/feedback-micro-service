# app/api/interview.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from db import schemas
from utils.dependencies import get_database
from bson import ObjectId
from db.schemas import PyObjectId  # Ensure PyObjectId is imported
from log.logging_config import logger
from ai_utils.chatbot_utils import AI_Generator
import copy

router = APIRouter(
    prefix="/interview",
    tags=["interview"],
    responses={404: {"description": "Not found"}},
)

ai_generator = AI_Generator()

# TODO: Get list of interviews a user has, paginations needds to be done 10 intervies per page. 
@router.get("/list/{user}", response_model=List[schemas.InterviewSummary])
async def list_user_interviews(user: str, skip: int = 0, limit: int = 10, db=Depends(get_database)):
    """
    Retrieves a paginated list of interviews for a specific user, returning only key information.
    10 interviews per page by default.
    """
    # Ensure valid pagination limit
    if limit <= 0:
        raise HTTPException(status_code=400, detail="Limit must be greater than zero.")
    
    # Fetch interviews for the specified user
    interviews = db.interviews.find({"user": user}, {
        "job_title": 1,
        "job_description": 1,
        "question_type": 1,
        "role_level": 1,
    }).skip(skip).limit(limit)
    
    # Convert each interview to the correct schema format
    interviews_list = []
    for interview in interviews:
        interview['_id'] = schemas.PyObjectId(interview['_id'])
        interviews_list.append(schemas.InterviewSummary(**interview))
    
    return interviews_list




@router.post("/generate-question", response_model=schemas.Interview)
async def create_interview(interview: schemas.InterviewCreate, db=Depends(get_database)):
    """
    Creates a new interview entry in MongoDB.
    """
    res = ai_generator.generate_questions(interview.get_combined_job_info())
    logger.debug(f"calling create_interview: {res}")
    interview_dict = interview.model_dump(by_alias=True)
    interview_dict['QAs'] = res['qas']
    result = db.interviews.insert_one(interview_dict)
    interview_dict["_id"] = PyObjectId(result.inserted_id)  # Convert to PyObjectId
    return schemas.Interview(**interview_dict)

@router.get("/get_interview/{user}/{interview_id}", response_model=schemas.Interview)
async def get_interview(user:str ,interview_id: str, db=Depends(get_database)):
    """
    Retrieves an interview by its ID.
    """
    if not ObjectId.is_valid(interview_id):
        raise HTTPException(status_code=400, detail="Invalid interview ID")
    
    interview = db.interviews.find_one({"_id": ObjectId(interview_id)})
    
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if user != interview['user']:
        raise HTTPException(status_code=403, detail="User does not have access to this interview")
    
    # Convert '_id' from ObjectId to PyObjectId
    interview['_id'] = schemas.PyObjectId(interview['_id'])
    return schemas.Interview(**interview)

@router.put("/generate_interview_feedback/{user}/{interview_id}", response_model=schemas.Interview)
async def generate_interview_feedback(
    user: str,
    interview_id: str,
    body: schemas.QuestionBody,
    db=Depends(get_database)
):
    """
    Updates an existing interview by adding feedback to a specific question.
    """
    if not ObjectId.is_valid(interview_id):
        raise HTTPException(status_code=400, detail="Invalid interview ID")
    
    # Fetch the interview document
    interview = db.interviews.find_one({"_id": ObjectId(interview_id)})
    
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Check if the user has access to this interview
    if user != interview.get('user'):
        raise HTTPException(status_code=403, detail="User does not have access to this interview")
    
    # Find the QA entry with the specified question
    qa_list = interview.get('QAs', [])
    qa_found = False
    
    # Convert '_id' to PyObjectId
    temp_interview = copy.copy(interview)
    temp_interview['_id'] = schemas.PyObjectId(temp_interview['_id'])
    
    # Initialize Pydantic model with corrected '_id'
    temp_interview = schemas.Interview(**temp_interview)
    
    for qa in qa_list:
        if qa.get('question') == body.question:
            
            # call ai model
            res = ai_generator.generate_q_feedback(
                # preparing the necessary info for feedback generation.
                temp_interview.get_combined_job_info() + "\n"*2  + body.get_combined_Q_info()
            )
            logger.debug(res)
            qa['original_user_answer'] = body.answer
            qa['ai_feedback'] = res['ai_feedback']
            qa['ai_modified_user_answer'] = res['ai_modified_user_answer']
            qa_found = True
            break
    del temp_interview, 
    if not qa_found:
        raise HTTPException(status_code=404, detail="Question not found in the interview")
    
    # Update the interview document in the database
    update_result = db.interviews.update_one(
        {"_id": ObjectId(interview_id)},
        {"$set": {"QAs": qa_list}}
    )
    
    if update_result.modified_count == 0:  # this when the key is not found or no change was made in the user response. No change in db anyways.
        raise HTTPException(status_code=500, detail="Failed to update the interview")
    
    # Fetch the updated interview document
    updated_interview = db.interviews.find_one({"_id": ObjectId(interview_id)})
    
    if updated_interview is None:
        raise HTTPException(status_code=404, detail="Interview not found after update")
    
    # Convert '_id' from ObjectId to PyObjectId
    updated_interview['_id'] = schemas.PyObjectId(updated_interview['_id'])
        
    return schemas.Interview(**updated_interview)

# @router.delete("/{interview_id}")
# async def delete_interview(interview_id: str, db=Depends(get_database)):
#     """
#     Deletes an interview from MongoDB.
#     """
#     if not ObjectId.is_valid(interview_id):
#         raise HTTPException(status_code=400, detail="Invalid interview ID")
#     result = db.interviews.delete_one({"_id": ObjectId(interview_id)})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Interview not found")
#     return {"message": "Interview deleted successfully"}

# @router.get("/", response_model=List[schemas.Interview])
# async def list_interviews(skip: int = 0, limit: int = 10, db=Depends(get_database)):
#     """
#     Retrieves a paginated list of interviews.
#     """
#     interviews = db.interviews.find().skip(skip).limit(limit)
#     return [schemas.Interview(**interview) for interview in interviews]
