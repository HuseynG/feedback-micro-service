# consumer/Dockerfile

FROM python:3.12-slim

# Install ODBC Driver and dependencies
RUN apt-get update && \
    apt-get install -y curl gnupg2 apt-transport-https && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set work directory to /consumer
WORKDIR /consumer

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY consumer.py .

# Note: Removed copying of app and .env as they are mounted via volumes and environment variables are managed via docker-compose.yml

# Start the consumer application
CMD ["python", "consumer.py"]
