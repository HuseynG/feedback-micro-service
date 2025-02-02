from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging
from typing import Optional

load_dotenv()

logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[MongoClient] = None
    db = None

    @classmethod
    def connect_to_mongodb(cls):
        """Connect to MongoDB and initialize databases"""
        mongodb_conn_str = os.getenv("MONGODB_CONN_STR")
        mongodb_db_name = os.getenv("MONGODB_DB_NAME", "PythonMicroserviceDB")
        
        if not mongodb_conn_str:
            raise ValueError("MONGODB_CONN_STR environment variable is not set")

        try:
            cls.client = MongoClient(mongodb_conn_str)
            cls.db = cls.client[mongodb_db_name]
            
            # Initialize collections
            cls.interviews = cls.db.get_collection("interviews")
            cls.company_insights = cls.db.get_collection("company_insights")
            
            cls.company_insights.create_index([("createdAt", 1)], expireAfterSeconds=3600*24*7)

            # Test the connection
            cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {mongodb_db_name}")
            
            return cls.db
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    def close_mongodb_connection(cls):
        """Close MongoDB connection"""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Closed MongoDB connection!")

    @classmethod
    def get_db(cls):
        """Get database instance"""
        if cls.db is None:
            return cls.connect_to_mongodb()
        return cls.db

    @classmethod
    def get_interviews(cls):
        """Get interviews collection"""
        db = cls.get_db()
        return db.interviews

    @classmethod
    def get_company_insights(cls):
        """Get company insights collection"""
        db = cls.get_db()
        return db.company_insights

# Create global instance
mongodb = MongoDB()
