# app/main.py
import os
import asyncio
from urllib.parse import quote_plus
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import SessionLocal, engine
import aio_pika

models.Base.metadata.create_all(bind=engine, checkfirst=True)

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# RabbitMQ connection
async def get_rabbitmq_connection():
    # Load RabbitMQ environment variables
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', '5672')
    RABBITMQ_DEFAULT_USER = os.getenv('RABBITMQ_DEFAULT_USER', 'guest')
    RABBITMQ_DEFAULT_PASS = os.getenv('RABBITMQ_DEFAULT_PASS', 'guest')

    # URL-encode username and password
    username = quote_plus(RABBITMQ_DEFAULT_USER)
    password = quote_plus(RABBITMQ_DEFAULT_PASS)

    RABBITMQ_URL = f"amqp://{username}:{password}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    return connection

@app.on_event("startup")
async def startup_event():
    app.state.rabbitmq_connection = await get_rabbitmq_connection()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.rabbitmq_connection.close()

@app.post("/items/", response_model=schemas.Item)
async def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = models.Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    # Publish message to RabbitMQ
    asyncio.create_task(publish_message(db_item.id))
    return db_item

@app.get("/items/{item_id}", response_model=schemas.Item)
async def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

async def publish_message(item_id):
    channel = await app.state.rabbitmq_connection.channel()
    queue = await channel.declare_queue('items_queue', durable=True)
    await channel.default_exchange.publish(
        aio_pika.Message(body=str(item_id).encode()),
        routing_key='items_queue'
    )
    await channel.close()
