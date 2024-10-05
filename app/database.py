# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

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

# Create the engine
engine = create_engine(DATABASE_URL, fast_executemany=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
