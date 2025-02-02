from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from api import router  # Import the main router from api/__init__.py
from database.mongodb import mongodb
from utils.auth import verify_api_key

# Create the lifespan manager to handle startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for handling application lifespan events (startup and shutdown).
    """
    # Startup logic
    app.database = mongodb.connect_to_mongodb()
    
    yield
    
    # Shutdown logic
    mongodb.close_mongodb_connection()

# Initialize FastAPI app with the lifespan protocol
app = FastAPI(title="Modular FastAPI Application", lifespan=lifespan, dependencies=[Depends(verify_api_key)])

# Include the main router that contains all other routers
app.include_router(router)
