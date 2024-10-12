# app/api/interview.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from db import schemas
from utils.dependencies import get_database
from bson import ObjectId
from db.schemas import PyObjectId  # Ensure PyObjectId is imported
from log.logging_config import logger
from ai_utils.chatbot_utils import AI_Generator

router = APIRouter(
    prefix="/interview",
    tags=["interview"],
    responses={404: {"description": "Not found"}},
)

ai_generator = AI_Generator()

@router.post("/", response_model=schemas.Interview)
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





# @router.get("/{interview_id}", response_model=schemas.Interview)
# async def get_interview(interview_id: str, db=Depends(get_database)):
#     """
#     Retrieves an interview by its ID.
#     """
#     if not ObjectId.is_valid(interview_id):
#         raise HTTPException(status_code=400, detail="Invalid interview ID")
#     interview = db.interviews.find_one({"_id": ObjectId(interview_id)})
#     if interview is None:
#         raise HTTPException(status_code=404, detail="Interview not found")
#     return schemas.Interview(**interview)

# @router.put("/{interview_id}", response_model=schemas.Interview)
# async def update_interview(interview_id: str, interview: schemas.InterviewCreate, db=Depends(get_database)):
#     """
#     Updates an existing interview in MongoDB.
#     """
#     if not ObjectId.is_valid(interview_id):
#         raise HTTPException(status_code=400, detail="Invalid interview ID")
#     result = db.interviews.update_one(
#         {"_id": ObjectId(interview_id)},
#         {"$set": interview.dict(by_alias=True)}
#     )
#     if result.matched_count == 0:
#         raise HTTPException(status_code=404, detail="Interview not found")
#     updated_interview = db.interviews.find_one({"_id": ObjectId(interview_id)})
#     return schemas.Interview(**updated_interview)

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
