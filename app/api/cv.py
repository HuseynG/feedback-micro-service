from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query, Path, Depends
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceExistsError
import os
from typing import Optional, Dict, Any
from core.config import settings
from datetime import datetime, timedelta
import logging
from ai_utils.cv_ai_chat_utils import DocumentProcessor
from ai_utils.cv_schema import ATSJobRequirement
import tempfile
import json
from pydantic import BaseModel
from database.mongodb import mongodb
from utils.dependencies import get_database

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cv",
    tags=["CV Management"],
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)

# Initialize Azure Blob Storage Client
blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
container_name = "cvs"  # Container name for storing CVs

try:
    container_client = blob_service_client.create_container(container_name)
except ResourceExistsError:
    container_client = blob_service_client.get_container_client(container_name)

def get_safe_filename(filename: str) -> str:
    """
    **Convert filename to a safe format for storage.**\n
    \n
    **Parameters:**\n
        - **filename**: Original filename to sanitize\n
    \n
    **Returns:**\n
        str: Sanitized filename containing only alphanumeric characters, dots, and underscores\n
    """
    # Keep only alphanumeric chars, dots, and underscores
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._")
    return safe_name.replace(" ", "_")

async def delete_existing_cvs(user_id: str) -> None:
    """
    **Delete all existing CVs for a specific user from storage.**\n
    \n
    **Parameters:**\n
        - **user_id**: ID of the user whose CVs should be deleted\n
    \n
    **Raises:**\n
        - **HTTPException (500)**: If deletion fails\n
    """
    try:
        blobs = container_client.list_blobs(name_starts_with=f"{user_id}/")
        for blob in blobs:
            blob_client = container_client.get_blob_client(blob.name)
            blob_client.delete_blob()
    except Exception as e:
        logger.error(f"Error deleting existing CVs for user {user_id}: {str(e)}")
        raise

class UploadCVData(BaseModel):
    file_name: str
    path: str
    content_type: str
    size: int
    cv_content: dict
    cv_analysis: Optional[dict] = None

class UploadCVResponse(BaseModel):
    status: str
    message: str
    data: UploadCVData

class GetCVResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict] = None
    cv_content: Optional[Dict] = None
    cv_analysis: Optional[Dict] = None
    download_url: Optional[str] = None
    file_name: Optional[str] = None
    last_modified: datetime

class DeleteCVResponse(BaseModel):
    status: str
    message: str

@router.post(
    "/{user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Upload CV",
    description="Upload or update a CV for the specified user. If a CV already exists, it will be deleted before uploading the new one.",
    response_description="Returns a success message, stored filename, and extracted CV content",
    response_model=UploadCVResponse
)
async def upload_cv(
    user_id: str = Path(..., description="ID of the user to upload CV for"),
    file: UploadFile = File(..., description="CV file (PDF only)"),
    db=Depends(get_database)
) -> UploadCVResponse:
    """
    **Upload or update a CV for a specific user.**\n
    \n
    **Parameters:**\n
        - **user_id**: ID of the user to upload CV for\n
        - **file**: CV file to upload (must be PDF)\n
    \n
    **Returns:**\n
        dict: Upload result containing:\n
        {\n
            **"message"**: str,      # Success message\n
            **"file_name"**: str,    # Original filename (sanitized)\n
            **"path"**: str,         # Full path in storage\n
            **"cv_content"**: dict,  # Extracted CV content and analysis\n
            **"cv_analysis"**: dict  # AI-generated CV analysis\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (400)**: If file format is invalid (not PDF)\n
        - **HTTPException (500)**: If upload fails\n
    """
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid file format",
                "error": "Only PDF files are supported"
            }
        )
    
    try:
        # Delete any existing CVs for this user
        await delete_existing_cvs(user_id)
        
        # Create temporary file to process CV
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file.flush()
            
            # Extract CV content using DocumentProcessor
            processor = DocumentProcessor()
            cv_content = await processor.extract_cv_content(temp_file.name)
            
            # Analyze CV
            cv_analysis = await processor.analyze_cv(temp_file.name)
            
            # Store CV content and analysis in MongoDB
            cv_data = {
                "user_id": user_id,
                "cv_content": cv_content.model_dump(mode='json'),  # Use model_dump with json mode to properly handle all types
                "cv_analysis": cv_analysis.model_dump(mode='json'),
                "filename": get_safe_filename(file.filename),
                "updated_at": datetime.utcnow()
            }
            
            db.cvs.update_one(
                {"user_id": user_id},
                {"$set": cv_data},
                upsert=True
            )
            
            # Upload the new CV
            safe_filename = get_safe_filename(file.filename)
            blob_name = f"{user_id}/{safe_filename}"
            blob_client = container_client.get_blob_client(blob_name)
            
            # Upload to blob storage
            blob_client.upload_blob(contents, overwrite=True)
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            return UploadCVResponse(
                status="success",
                message=f"CV '{safe_filename}' uploaded successfully",
                data=UploadCVData(
                    file_name=safe_filename,
                    path=blob_name,
                    content_type=file.content_type,
                    size=len(contents),
                    cv_content=cv_content.model_dump(mode='json'),
                    cv_analysis=cv_analysis.model_dump(mode='json')
                )
            )
    except Exception as e:
        logger.error(f"Failed to upload CV for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to upload CV",
                "error": str(e)
            }
        )

@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Get CV",
    description="Get CV information and generate a download URL for the specified user",
    response_description="Returns CV information and download URL",
    response_model=GetCVResponse
)
async def get_cv(
    user_id: str = Path(..., description="ID of the user to get CV for"),
    db=Depends(get_database)
) -> GetCVResponse:
    """
    **Get CV information and generate a download URL for a specific user.**\n
    \n
    **Parameters:**\n
        - **user_id**: ID of the user to get CV for\n
    \n
    **Returns:**\n
        GetCVResponse: CV information containing:\n
        {\n
            **"status"**: str,           # Status of the operation\n
            **"message"**: str,          # Success message\n
            **"data"**: dict,            # CV metadata\n
            **"cv_content"**: dict,      # Extracted CV content\n
            **"cv_analysis"**: dict,     # AI-generated CV analysis\n
            **"download_url"**: str,     # Temporary download URL\n
            **"file_name"**: str,        # Original filename\n
            **"last_modified"**: datetime # Last modification time\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (404)**: If no CV is found for the user\n
        - **HTTPException (500)**: If retrieval fails\n
    """
    try:
        # Get CV data from MongoDB
        cv_data = db.cvs.find_one({"user_id": user_id})
        if not cv_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "CV not found",
                    "error": f"No CV found for user {user_id}"
                }
            )

        # List blobs to get CV file info
        blobs = container_client.list_blobs(name_starts_with=f"{user_id}/")
        cv_blob = next(blobs, None)
        
        if not cv_blob:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "CV file not found",
                    "error": f"No CV file found in storage for user {user_id}"
                }
            )

        # Generate SAS token for temporary download URL
        sas_token = generate_blob_sas(
            account_name=container_client.account_name,
            container_name=container_client.container_name,
            blob_name=cv_blob.name,
            account_key=container_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=30)
        )

        download_url = f"{container_client.url}/{cv_blob.name}?{sas_token}"

        return GetCVResponse(
            status="success",
            message=f"CV information retrieved successfully for user {user_id}",
            data={
                "size": cv_blob.size,
                "content_type": cv_blob.content_settings.content_type,
                "path": cv_blob.name
            },
            cv_content=cv_data.get("cv_content"),
            cv_analysis=cv_data.get("cv_analysis"),
            download_url=download_url,
            file_name=cv_data.get("filename"),
            last_modified=cv_blob.last_modified
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to get CV for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to get CV",
                "error": str(e)
            }
        )

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete CV",
    description="Delete a user's CV from both storage and database.",
    response_description="Returns success message on deletion",
    response_model=DeleteCVResponse
)
async def delete_cv(
    user_id: str = Path(..., description="ID of the user to delete CV for"),
    db=Depends(get_database)
) -> DeleteCVResponse:
    """
    **Delete a user's CV from storage and database.**\n
    \n
    **Parameters:**\n
        - **user_id**: ID of the user to delete CV for\n
    \n
    **Returns:**\n
        DeleteCVResponse: Operation result containing:\n
        {\n
            **"status"**: str,   # Status of the operation\n
            **"message"**: str   # Success message\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (404)**: If no CV is found for the user\n
        - **HTTPException (500)**: If deletion fails\n
    """
    # First check if CV exists in MongoDB
    cv_data = db.cvs.find_one({"user_id": user_id})
    if not cv_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "CV not found",
                "error": f"No CV found for user {user_id}"
            }
        )

    try:
        # Delete from MongoDB first
        db.cvs.delete_one({"user_id": user_id})
        
        # Then delete from Azure Blob Storage
        deleted = False
        blobs = container_client.list_blobs(name_starts_with=f"{user_id}/")
        for blob in blobs:
            blob_client = container_client.get_blob_client(blob.name)
            blob_client.delete_blob()
            deleted = True
        
        if not deleted:
            logger.warning(f"No CV files found in storage for user {user_id}")
        
        return DeleteCVResponse(
            status="success",
            message=f"CV for user {user_id} deleted successfully"
        )
            
    except Exception as e:
        logger.error(f"Failed to delete CV for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to delete CV",
                "error": str(e)
            }
        )
