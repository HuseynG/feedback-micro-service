# app/api/items.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from db import schemas, models
from db.database import SessionLocal
from core.messaging import publish_message
import asyncio

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get DB session
def get_db():
    """
    Provides a database session to the endpoint.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Item)
async def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db), request: Request = None):
    """
    Creates a new item and publishes its ID to RabbitMQ.
    """
    db_item = models.Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    # Publish message to RabbitMQ
    if request:
        asyncio.create_task(publish_message(
            request.app.state.rabbitmq_connection, 
            'items_queue', 
            str(db_item.id)
        ))
    return db_item

@router.get("/{item_id}", response_model=schemas.Item)
async def read_item(item_id: int, db: Session = Depends(get_db)):
    """
    Retrieves an item by its ID.
    """
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item
