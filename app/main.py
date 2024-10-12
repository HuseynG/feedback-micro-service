from fastapi import FastAPI
from contextlib import asynccontextmanager
from api import interview  # Import your interview router
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Create the lifespan manager to handle startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for handling application lifespan events (startup and shutdown).
    """
    # Startup logic
    mongodb_conn_str = os.getenv("MONGODB_CONN_STR")
    mongodb_db_name = os.getenv("MONGODB_DB_NAME", "feedback_db")
    
    if not mongodb_conn_str:
        raise ValueError("MONGODB_CONN_STR environment variable is not set")
    
    app.mongodb_client = MongoClient(mongodb_conn_str)
    app.database = app.mongodb_client[mongodb_db_name]
    print(f"Connected to MongoDB database: {mongodb_db_name}")
    
    # This yield lets the app run while the connection is active
    yield
    
    # Shutdown logic
    app.mongodb_client.close()
    print("Disconnected from MongoDB!")

# Initialize FastAPI app with the lifespan protocol
app = FastAPI(title="Modular FastAPI Application", lifespan=lifespan)

# Include API routers
app.include_router(interview.router)
