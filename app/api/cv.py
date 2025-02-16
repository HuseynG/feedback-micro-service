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

class UploadCVResponse(BaseModel):
    status: str
    message: str
    data: UploadCVData

class GetCVResponse(BaseModel):
    download_url: str
    file_name: str
    content_type: str
    size: int
    last_modified: datetime
    cv_content: Optional[Dict] = None

@router.post(
    "/upload/{user_id}",
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
            **"cv_content"**: dict   # Extracted CV content and analysis\n
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
                "error": "File must be a PDF document",
                "accepted_formats": ["PDF"]
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
            
            # Store CV content in MongoDB
            cv_data = {
                "user_id": user_id,
                "cv_content": cv_content.model_dump(mode='json'),  # Use model_dump with json mode to properly handle all types
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
                    cv_content=cv_content.model_dump(mode='json')
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
    summary="Get CV",
    description="Retrieve a user's CV. Returns the download URL, file metadata, and parsed CV content.",
    response_description="Returns CV URL, metadata, and content if found",
    response_model=GetCVResponse
)
async def get_cv(
    user_id: str = Path(..., description="ID of the user to get CV for"),
    db=Depends(get_database)
) -> GetCVResponse:
    """
    **Retrieve a user's CV from storage.**\n
    \n
    **Parameters:**\n
        - **user_id**: ID of the user to get CV for\n
    \n
    **Returns:**\n
        GetCVResponse: CV information containing:\n
        {\n
            **"download_url"**: str,      # Temporary download URL for the CV (valid for 1 hour)\n
            **"file_name"**: str,         # Original filename\n
            **"content_type"**: str,      # File MIME type\n
            **"size"**: int,              # File size in bytes\n
            **"last_modified"**: datetime, # Last modification timestamp\n
            **"cv_content"**: dict        # Parsed CV content from database\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (404)**: If no CV is found for the user\n
        - **HTTPException (500)**: If retrieval fails\n
    """
    # Get CV content from MongoDB
    cv_data = db.cvs.find_one({"user_id": user_id})
    if not cv_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "CV not found",
                "error": f"No CV found for user {user_id}"
            }
        )

    # List all blobs in the user's directory
    try:
        blobs = container_client.list_blobs(name_starts_with=f"{user_id}/")
        blob_list = list(blobs)
        
        if not blob_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "CV not found",
                    "error": f"No CV found for user {user_id}"
                }
            )
        
        # Get the most recently modified blob
        latest_blob = max(blob_list, key=lambda x: x.last_modified)
        blob_client = container_client.get_blob_client(latest_blob.name)
        
        properties = blob_client.get_blob_properties()
        
        # Generate SAS token for temporary access (1 hour)
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=latest_blob.name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Construct download URL with SAS token
        download_url = f"{blob_client.url}?{sas_token}"
        
        return GetCVResponse(
            download_url=download_url,
            file_name=latest_blob.name.split('/')[-1],
            content_type=properties.content_settings.content_type,
            size=properties.size,
            last_modified=properties.last_modified,
            cv_content=cv_data.get('cv_content')
        )
        
    except Exception as e:
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
    description="Delete a user's CV from storage.",
    response_description="Returns success message on deletion"
)
async def delete_cv(
    user_id: str = Path(..., description="ID of the user to delete CV for")
) -> Dict[str, str]:
    """
    **Delete a user's CV from storage.**\n
    \n
    **Parameters:**\n
        - **user_id**: ID of the user to delete CV for\n
    \n
    **Returns:**\n
        dict: Operation result containing:\n
        {\n
            **"status"**: str,   # Status of the operation\n
            **"message"**: str   # Success message\n
        }\n
    \n
    **Raises:**\n
        - **HTTPException (404)**: If no CV is found for the user\n
        - **HTTPException (500)**: If deletion fails\n
    """
    deleted = False
    try:
        # List and delete all blobs in the user's directory
        blobs = container_client.list_blobs(name_starts_with=f"{user_id}/")
        for blob in blobs:
            blob_client = container_client.get_blob_client(blob.name)
            blob_client.delete_blob()
            deleted = True
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "CV not found",
                    "error": f"No CV found for user {user_id}"
                }
            )
        
        # Delete CV content from MongoDB
        mongodb.cvs.delete_one({"user_id": user_id})
        
        return {
            "status": "success",
            "message": f"CV for user {user_id} deleted successfully"
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to delete CV for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to delete CV",
                "error": str(e)
            }
        )
