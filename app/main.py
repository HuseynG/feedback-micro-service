# app/main.py
from fastapi import FastAPI
from api import items
from db.database import init_db
from core.messaging import get_rabbitmq_connection
from core.config import settings

app = FastAPI(title="Modular FastAPI Application")

# Include API routers
app.include_router(items.router)

@app.on_event("startup")
async def startup_event():
    """
    Event handler for application startup.
    Initializes the database and establishes RabbitMQ connection.
    """
    # Initialize the database
    init_db()
    # Establish RabbitMQ connection
    app.state.rabbitmq_connection = await get_rabbitmq_connection()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Event handler for application shutdown.
    Closes the RabbitMQ connection.
    """
    await app.state.rabbitmq_connection.close()
