from fastapi import APIRouter

router = APIRouter(
    prefix="/company_insights",
    tags=["company_insights"],
    responses={404: {"description": "Not found"}},
)

@router.get("/hello")
async def get_hello_world():
    """
    A simple hello world endpoint for testing company insights.
    """
    return {"message": "Hello from Company Insights!"} 