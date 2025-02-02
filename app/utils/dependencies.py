# app/utils/dependencies.py
from fastapi import Request
from database.mongodb import mongodb

def get_database():
    """
    Dependency to get the MongoDB database instance.
    Returns the database with initialized collections.
    """
    db = mongodb.get_db()
    # Collections are already initialized in the MongoDB class
    return db
