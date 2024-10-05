# app/Dockerfile

FROM python:3.10-slim

# Install ODBC Driver and dependencies
RUN apt-get update && \
    apt-get install -y curl gnupg2 apt-transport-https && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set work directory to /app
WORKDIR /app

# Copy requirements to the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app code to the container
COPY . .

# Set PYTHONPATH to include the root directory
ENV PYTHONPATH=/

# Expose port 8000
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
