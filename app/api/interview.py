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

@router.get("/list/{user_id}", response_model=List[schemas.InterviewSummary])
async def list_user_interviews(user_id: str, skip: int = 0, limit: int = 10, db=Depends(get_database)):
    """
    **Retrieve a paginated list of interviews for a specific user.**\n
    \n
    **Parameters:**\n
        - **user_id**: The unique identifier of the user\n
        - **skip**: Number of records to skip for pagination (default: 0)\n
        - **limit**: Maximum number of records to return (default: 10)\n
    \n
    **Returns:**\n
        List of interview summaries containing:\n
        {\n
            **"interview_id"**: str,  # Unique identifier of the interview\n
            **"job_title"**: str,     # Title of the job\n
            **"job_description"**: str,  # Description of the job\n
            **"question_type"**: str,    # Type of interview questions\n
            **"role_level"**: str        # Level of the role\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (400)**: If pagination parameters are invalid\n
        - **HTTPException (404)**: If no interviews are found for the user\n
    """
    # Ensure valid pagination limit
    if limit <= 0 or skip < 0:
        raise HTTPException(status_code=400, detail="Pagination limit and skip must be greater than zero.")
    
    # Fetch interviews for the specified user
    interviews = db.interviews.find({"user_id": user_id}, {
        "job_title": 1,
        "job_description": 1,
        "question_type": 1,
        "role_level": 1,
    }).skip(skip).limit(limit)
    
    interviews_list = []
    for interview in interviews:
        interview['interview_id'] = str(schemas.PyObjectId(interview['_id']))
        interviews_list.append(schemas.InterviewSummary(**interview))
    
    # If no interviews found, return 404
    if not interviews_list:
        raise HTTPException(status_code=404, detail="No interviews found for the user_id.")
    
    return interviews_list

@router.post("/generate-question", response_model=schemas.Interview)
async def create_interview(interview: schemas.InterviewCreate, db=Depends(get_database)):
    """
    **Create a new interview with AI-generated questions based on job details.**\n
    \n
    **Parameters:**\n
        Interview creation object containing:\n
        {\n
            **"user_id"**: str,          # ID of the user\n
            **"job_title"**: str,        # Title of the job position\n
            **"job_description"**: str,   # Description of the job\n
            **"question_type"**: str,     # Type of questions to generate\n
            **"role_level"**: str         # Level of the role\n
        }\n
    \n
    **Returns:**\n
        Created interview object containing:\n
        {\n
            **"interview_id"**: str,      # Unique identifier\n
            **"user_id"**: str,           # ID of the user\n
            **"job_title"**: str,         # Title of the job\n
            **"job_description"**: str,   # Description of the job\n
            **"QAs"**: List[dict]         # List of generated questions and answers\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (400)**: If required fields are missing\n
        - **HTTPException (500)**: If question generation fails\n
    """
    # Ensure all required fields are present in the schema
    if not interview.job_title and not interview.job_description:
        raise HTTPException(status_code=400, detail="Job title or description type are required fields.")
    
    try:
        res = ai_generator.generate_questions(interview.get_combined_job_info())
    except Exception as e:
        logger.error(f"AI question generation failed: {e}")
        raise HTTPException(status_code=500, detail="Error generating questions.")
    
    interview_dict = interview.model_dump(by_alias=True)
    interview_dict['QAs'] = res['qas']
    
    result = db.interviews.insert_one(interview_dict)
    
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to create interview in the database.")
    
    interview_dict["_id"] = PyObjectId(result.inserted_id)  # Convert to PyObjectId
    return schemas.Interview(**interview_dict)

@router.get("/get_interview/{user_id}/{interview_id}", response_model=schemas.Interview)
async def get_interview(user_id: str, interview_id: str, db=Depends(get_database)):
    """
    **Retrieve a specific interview by its ID.**\n
    \n
    **Parameters:**\n
        - **user_id**: ID of the user requesting the interview\n
        - **interview_id**: Unique identifier of the interview to retrieve\n
    \n
    **Returns:**\n
        Complete interview object containing:\n
        {\n
            **"interview_id"**: str,      # Unique identifier of the interview\n
            **"user_id"**: str,           # ID of the user\n
            **"job_title"**: str,         # Title of the job\n
            **"job_description"**: str,   # Description of the job\n
            **"QAs"**: List[dict]         # List of questions and answers\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (400)**: If interview_id is invalid\n
        - **HTTPException (403)**: If user doesn't have access to the interview\n
        - **HTTPException (404)**: If interview is not found\n
    """
    # Validate interview_id
    if not ObjectId.is_valid(interview_id):
        raise HTTPException(status_code=400, detail="Invalid interview ID")
    
    interview = db.interviews.find_one({"_id": ObjectId(interview_id)})
    
    # If interview is not found
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # If the user does not have access to this interview
    if user_id != interview['user_id']:
        raise HTTPException(status_code=403, detail="User does not have access to this interview")
    
    interview['_id'] = schemas.PyObjectId(interview['_id'])
    
    return schemas.Interview(**interview)

@router.put("/generate_interview_feedback/{user_id}/{interview_id}", response_model=schemas.QA)
async def generate_interview_feedback(user_id: str, interview_id: str, body: schemas.QuestionBody, db=Depends(get_database)):
    """
    **Generate AI feedback for a user's interview answer.**\n
    \n
    **Parameters:**\n
        - **user_id**: ID of the user requesting feedback\n
        - **interview_id**: ID of the interview\n
        - **body**: Feedback request containing:\n
            {\n
                **"question"**: str,  # Question for which feedback is requested\n
                **"answer"**: str     # User's answer to the question\n
            }\n
    \n
    **Returns:**\n
        Updated question and answer object:\n
        {\n
            **"question"**: str,                 # Original question\n
            **"original_user_answer"**: str,     # User's provided answer\n
            **"ai_feedback"**: str,              # AI-generated feedback\n
            **"ai_modified_user_answer"**: str   # AI-modified user answer\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (400)**: If interview_id is invalid\n
        - **HTTPException (403)**: If user doesn't have access\n
        - **HTTPException (404)**: If interview or question not found\n
        - **HTTPException (500)**: If feedback generation fails\n
    """
    # Validate interview_id
    if not ObjectId.is_valid(interview_id):
        raise HTTPException(status_code=400, detail="Invalid interview ID")
    
    # Fetch the interview document
    interview = db.interviews.find_one({"_id": ObjectId(interview_id)})
    
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Check if the user has access to this interview
    if user_id != interview.get('user_id'):
        raise HTTPException(status_code=403, detail="User does not have access to this interview")
    
    # Ensure 'QAs' exist in the interview
    if 'QAs' not in interview or not interview['QAs']:
        raise HTTPException(status_code=404, detail="No QA entries found in the interview.")
    
    # Find the QA entry with the specified question or its follow-up
    qa_list = interview.get('QAs', [])
    qa_found = False
    followup_found = False
    
    # Validate body content for feedback generation
    if not body.question or not body.answer:
        raise HTTPException(status_code=400, detail="Both question and answer must be provided.")
    
    # Copy the interview and update '_id'
    temp_interview = copy.copy(interview)
    temp_interview['_id'] = schemas.PyObjectId(temp_interview['_id'])
    
    # Initialize Pydantic model with corrected '_id'
    temp_interview = schemas.Interview(**temp_interview)

    # Iterate through each question (QA) in the list
    for qa in qa_list:
        # Check if the provided question matches the main question
        if qa.get('question') == body.question:
            qa_found = True
            
            # Generate feedback for the main question            
            main_feedback = ai_generator.generate_q_feedback(
                temp_interview.get_combined_job_info()+ " | " + body.get_combined_Q_info()
            )
            logger.debug(main_feedback)
            
            # Update the main question with feedback and AI-modified answer
            qa['original_user_answer'] = body.answer
            qa['ai_feedback'] = main_feedback['ai_feedback']
            qa['ai_modified_user_answer'] = main_feedback['ai_modified_user_answer']
            
            break  # We found the main question, so we can exit the loop

        # If the main question doesn't match, check its follow-up questions
        followup_qas = qa.get('followup_qas', [])  # Safely access followup_qas with .get()
        for followup in followup_qas:
            if followup.get('question') == body.question:
                followup_found = True
                
                # Generate feedback for the follow-up question
                followup_feedback = ai_generator.generate_q_feedback(
                    temp_interview.get_combined_job_info()+ " | " + body.get_combined_Q_info()
                )
                
                # Update follow-up question with feedback and AI-modified answer
                followup['original_user_answer'] = body.answer
                followup['ai_feedback'] = followup_feedback['ai_feedback']
                followup['ai_modified_user_answer'] = followup_feedback['ai_modified_user_answer']

                break  # We found the follow-up question, so we can exit the inner loop

        if followup_found:
            break  # Exit the outer loop if we found a follow-up question

    if not qa_found and not followup_found:
        raise HTTPException(status_code=404, detail="Question or follow-up question not found in the interview.")
    
    # Update the interview document in the database
    update_result = db.interviews.update_one(
        {"_id": ObjectId(interview_id)},
        {"$set": {"QAs": qa_list}}
    )
    
    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update the interview with feedback.")
    
    # Fetch the updated interview document
    updated_interview = db.interviews.find_one({"_id": ObjectId(interview_id)})
    
    if updated_interview is None:
        raise HTTPException(status_code=404, detail="Interview not found after update")
    
    # Convert '_id' from ObjectId to PyObjectId
    updated_interview['_id'] = schemas.PyObjectId(updated_interview['_id'])
        
    # Find the updated QA entry
    qa_item = None
    if qa_found:
        qa_item = next((qa for qa in updated_interview["QAs"] if qa["question"] == body.question), None)
    elif followup_found:
        for qa in updated_interview["QAs"]:
            followup_item = next((f for f in qa.get("followup_qas", []) if f["question"] == body.question), None)
            if followup_item:
                qa_item = followup_item
                break

    if not qa_item:
        raise HTTPException(status_code=404, detail="Question not found in updated interview.")
    
    return schemas.QA(**qa_item)

@router.put("/follow-up/{user_id}/{interview_id}", response_model=List[schemas.FollowupQA])
async def generate_followup_questions(user_id: str, interview_id: str, body: schemas.QuestionBody, db=Depends(get_database)):
    """
    **Generate follow-up questions for a specific interview question.**\n
    \n
    **Parameters:**\n
        - **user_id**: ID of the user requesting follow-ups\n
        - **interview_id**: ID of the interview\n
        - **body**: Request containing:\n
            {\n
                **"question"**: str  # Question for which follow-ups are requested\n
            }\n
    \n
    **Returns:**\n
        List of follow-up questions:\n
        [\n
            {\n
                **"question"**: str,                 # Follow-up question\n
                **"original_user_answer"**: str,     # User's answer\n
                **"ideal_answer"**: str,             # Ideal answer\n
                **"ai_feedback"**: str,              # AI-generated feedback\n
                **"ai_modified_user_answer"**: str   # AI-modified answer\n
            }\n
        ]\n
    \n
    **Raises:**\n
        - **HTTPException (400)**: If interview_id is invalid\n
        - **HTTPException (403)**: If user doesn't have access\n
        - **HTTPException (404)**: If interview or question not found\n
    """
    # Validate interview_id
    if not ObjectId.is_valid(interview_id):
        raise HTTPException(status_code=400, detail="Invalid interview ID")
    
    # Fetch the interview document
    interview = db.interviews.find_one({"_id": ObjectId(interview_id)})
    
    # If interview is not found
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # If the user does not have access to this interview
    if user_id != interview.get('user_id'):
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
                temp_interview.get_combined_job_info()+ " | " + body.get_combined_Q_info()
            )
            
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
            
            # If the database update fails (e.g., no modification made)
            if update_result.modified_count == 0:
                raise HTTPException(status_code=500, detail="Failed to update the interview")
            
            # Return the newly generated follow-up QAs
            return followup_qas

    # If no QA is found for the provided question
    if not qa_found:
        raise HTTPException(status_code=404, detail="Question not found in the interview")
    
    # Default case: Return an empty list if no follow-up questions were added
    return []

@router.delete("/delete-interview/{user}/{interview_id}")
async def delete_interview(interview_id: str, db=Depends(get_database)):
    """
    **Delete an interview from the database.**\n
    \n
    **Parameters:**\n
        - **interview_id**: Unique identifier of the interview to delete\n
    \n
    **Returns:**\n
        {\n
            **"message"**: "Interview deleted successfully"\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (400)**: If interview_id is invalid\n
        - **HTTPException (404)**: If interview is not found\n
    """
    if not ObjectId.is_valid(interview_id):
        raise HTTPException(status_code=400, detail="Invalid interview ID")
    result = db.interviews.delete_one({"_id": ObjectId(interview_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Interview not found")
    return {"message": "Interview deleted successfully"}
