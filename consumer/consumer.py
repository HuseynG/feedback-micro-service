import os
import asyncio
import logging
from urllib.parse import quote_plus
import aio_pika
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import the Item model and Base class from the app module
from app.db.models import Item  # Import the Item model from the app
from app.db.database import Base  # Import the Base class

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('../.env')

# Load Azure SQL DB environment variables
AZURE_SQL_DRIVER = os.getenv('AZURE_SQL_DRIVER', 'ODBC Driver 18 for SQL Server')
AZURE_SQL_SERVER = os.getenv('AZURE_SQL_SERVER')
AZURE_SQL_PORT = os.getenv('AZURE_SQL_PORT', '1433')
AZURE_SQL_DATABASE = os.getenv('AZURE_SQL_DATABASE')
AZURE_SQL_USERNAME = os.getenv('AZURE_SQL_USERNAME')
AZURE_SQL_PASSWORD = os.getenv('AZURE_SQL_PASSWORD')
AZURE_SQL_ENCRYPT = os.getenv('AZURE_SQL_ENCRYPT', 'yes')
AZURE_SQL_TRUST_CERTIFICATE = os.getenv('AZURE_SQL_TRUST_CERTIFICATE', 'no')
TIMEOUT = os.getenv('TIMEOUT', '30')

# URL-encode the driver name and password
driver = quote_plus(AZURE_SQL_DRIVER)
password = quote_plus(AZURE_SQL_PASSWORD)

# Construct the DATABASE_URL
DATABASE_URL = (
    f"mssql+pyodbc://{AZURE_SQL_USERNAME}:{password}"
    f"@{AZURE_SQL_SERVER}:{AZURE_SQL_PORT}/{AZURE_SQL_DATABASE}"
    f"?driver={driver}&Encrypt={AZURE_SQL_ENCRYPT}"
    f"&TrustServerCertificate={AZURE_SQL_TRUST_CERTIFICATE}"
    f"&Connection Timeout={TIMEOUT}"
)

# Log the connection string details (but don't log sensitive data like passwords)
logger.info(f"DATABASE_URL: {DATABASE_URL}")
# Set up database connection
try:
    engine = create_engine(DATABASE_URL, fast_executemany=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Ensure tables are created
    Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.info("Connected successfully to Azure SQL Database")
except Exception as e:
    logger.error(f"Failed to connect to Azure SQL Database: {str(e)}")


# RabbitMQ connection
async def get_rabbitmq_connection():
    try:
        # Load RabbitMQ environment variables
        RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
        RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', '5672')
        RABBITMQ_DEFAULT_USER = os.getenv('RABBITMQ_DEFAULT_USER', 'guest')
        RABBITMQ_DEFAULT_PASS = os.getenv('RABBITMQ_DEFAULT_PASS', 'guest')

        # URL-encode username and password
        username = quote_plus(RABBITMQ_DEFAULT_USER)
        password = quote_plus(RABBITMQ_DEFAULT_PASS)

        RABBITMQ_URL = f"amqp://{username}:{password}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

        logger.info(f"Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        logger.info("Connected to RabbitMQ successfully")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        raise

async def consume_messages():
    try:
        connection = await get_rabbitmq_connection()
        channel = await connection.channel()
        queue = await channel.declare_queue('items_queue', durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    item_id = int(message.body.decode())
                    logger.info(f"Received message for item_id: {item_id}")
                    # Process the message
                    db = SessionLocal()
                    try:
                        item = db.query(Item).filter(Item.id == item_id).first()
                        if item:
                            # Perform some processing on the item
                            logger.info(f"Processing item: {item.name}")
                        else:
                            logger.warning(f"Item with id {item_id} not found.")
                    finally:
                        db.close()
    except Exception as e:
        logger.error(f"Error consuming messages: {str(e)}")
        await asyncio.sleep(5)  # Wait before retrying

async def main():
    await consume_messages()

if __name__ == "__main__":
    asyncio.run(main())
