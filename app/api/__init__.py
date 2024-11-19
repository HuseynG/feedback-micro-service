from fastapi import APIRouter
from .interview import router as interview_router
from .company_insights import router as company_insights_router

router = APIRouter()

router.include_router(interview_router)
router.include_router(company_insights_router)
