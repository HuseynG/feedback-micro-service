# app/main.py
from fastapi import FastAPI
from api import interview  # Import your interview router
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = FastAPI(title="Modular FastAPI Application")

# Include API routers
app.include_router(interview.router)

@app.on_event("startup")
def startup_db_client():
    """
    Event handler for application startup.
    Initializes the MongoDB client.
    """
    mongodb_conn_str = os.getenv("MONGODB_CONN_STR")
    mongodb_db_name = os.getenv("MONGODB_DB_NAME", "feedback_db")
    if not mongodb_conn_str:
        raise ValueError("MONGODB_CONN_STR environment variable is not set")
    app.mongodb_client = MongoClient(mongodb_conn_str)
    app.database = app.mongodb_client[mongodb_db_name]
    print(f"Connected to MongoDB database: {mongodb_db_name}")

@app.on_event("shutdown")
def shutdown_db_client():
    """
    Event handler for application shutdown.
    Closes the MongoDB client.
    """
    app.mongodb_client.close()
    print("Disconnected from MongoDB!") 
