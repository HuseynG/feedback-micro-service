# alembic/env.py

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add the project root to sys.path to ensure 'app' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set up loggers from the config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your application's Base metadata
from app.models import Base

# Set the target metadata for 'autogenerate' support
target_metadata = Base.metadata

# Construct the DATABASE_URL from environment variables
driver = os.getenv('AZURE_SQL_DRIVER', 'ODBC Driver 18 for SQL Server')
username = os.getenv('AZURE_SQL_USERNAME')
password = os.getenv('AZURE_SQL_PASSWORD')
server = os.getenv('AZURE_SQL_SERVER')
port = os.getenv('AZURE_SQL_PORT', '1433')
database = os.getenv('AZURE_SQL_DATABASE')
encrypt = os.getenv('AZURE_SQL_ENCRYPT', 'yes')
trust_cert = os.getenv('AZURE_SQL_TRUST_CERTIFICATE', 'no')
timeout = os.getenv('TIMEOUT', '30')

# URL-encode the driver name by replacing spaces with '+' signs
driver_encoded = driver.replace(' ', '+')

# Construct the full DATABASE_URL
DATABASE_URL = (
    f"mssql+pyodbc://{username}:{password}@{server}:{port}/{database}"
    f"?driver={driver_encoded}"
    f"&Encrypt={encrypt}"
    f"&TrustServerCertificate={trust_cert}"
    f"&Connection Timeout={timeout}"
)

# Set the SQLAlchemy URL in Alembic's config
config.set_main_option('sqlalchemy.url', DATABASE_URL)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect type changes
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect type changes
        )

        with context.begin_transaction():
            context.run_migrations()

# Determine whether to run in offline or online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
