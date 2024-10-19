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
import random

router = APIRouter(
    prefix="/interview",
    tags=["interview"],
    responses={404: {"description": "Not found"}},
)

ai_generator = AI_Generator()

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
        interview['interview_id'] = str(schemas.PyObjectId(interview['_id']))
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
async def get_interview(user: str, interview_id: str, db=Depends(get_database)):
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

@router.put("/generate_interview_feedback/{user}/{interview_id}", response_model=schemas.QA)
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
        
    qa_item = next((qa for qa in updated_interview["QAs"] if qa["question"] == body.question), None)
    if not qa_item:
        raise HTTPException(status_code=404, detail="Question not found in updated interview")
    return schemas.QA(**qa_item)

@router.put("/follow-up/{user}/{interview_id}", response_model=List[schemas.FollowupQA])
async def generate_followup_questions(
    user: str,
    interview_id: str,
    body: schemas.QuestionBody,
    db=Depends(get_database)
):
    """
    Updates an existing interview by adding follow-up to a specific question and returns follow-up questions.
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
    followup_qas = []  # Initialize this outside the loop for returning later

    # Convert '_id' to PyObjectId
    temp_interview = copy.copy(interview)
    temp_interview['_id'] = schemas.PyObjectId(temp_interview['_id'])
    
    # Initialize Pydantic model with corrected '_id'
    temp_interview = schemas.Interview(**temp_interview)

    for qa in qa_list:
        if qa.get('question') == body.question:
            qa_found = True
            
            # Count the existing follow-up questions
            existing_followups = qa.get('followup_qas', [])
            followup_count = len(existing_followups)
            
            # If there are already 25 or more follow-up questions
            if followup_count >= 25:
                # Filter unanswered follow-ups (where original_user_answer is None or empty)
                unanswered_followups = [f for f in existing_followups if not f.get('original_user_answer')]
                
                # If no unanswered follow-ups, return an empty list
                if not unanswered_followups:
                    return []
                
                # Select a random sample of unanswered follow-ups (e.g., 5 questions)
                random_selection = random.sample(unanswered_followups, min(5, len(unanswered_followups)))
                
                # Return the randomly selected unanswered follow-ups
                return random_selection
            
            # Generate follow-up questions if the count is less than 25
            res = ai_generator.generate_follow_up_qs(
                temp_interview.get_combined_job_info() + "\n" * 2 + body.get_combined_Q_info()
            )
            logger.debug(f"res: {res}")
            
            # Collect existing follow-up questions to ensure uniqueness
            existing_questions = {f['question'] for f in existing_followups}

            # Assuming `res` contains a list of follow-up questions and their feedback
            for followup in res['followup_qas']:
                if followup['question'] not in existing_questions:
                    ai_feedback_data = followup.get('ai_feedback', None)
                    
                    followup_qa = schemas.FollowupQA(
                        question=followup['question'],
                        original_user_answer=followup.get('original_user_answer', ""),
                        ideal_answer=followup.get('ideal_answer'),
                        ai_feedback=schemas.QA_Feedback_Model(**ai_feedback_data) if ai_feedback_data else None,
                        ai_modified_user_answer=followup.get('ai_modified_user_answer')
                    )

                    # Use model_dump() to convert the FollowupQA Pydantic object to a dictionary
                    followup_qas.append(followup_qa.model_dump())

            # Update the specific QA's follow-up questions list by appending new ones
            update_result = db.interviews.update_one(
                {"_id": ObjectId(interview_id), "QAs.question": body.question},
                {"$push": {"QAs.$.followup_qas": {"$each": followup_qas}}}  # Append new follow-ups instead of replacing the list
            )
            
            if update_result.modified_count == 0:
                raise HTTPException(status_code=500, detail="Failed to update the interview")
            
            # Return the newly generated follow-up QAs
            return followup_qas

    if not qa_found:
        raise HTTPException(status_code=404, detail="Question not found in the interview")
    
    # If no updates were needed, return an empty list (default behavior)
    return []





# TODO: Delete an interview
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
