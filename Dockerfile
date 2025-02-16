FROM python:3.12-slim

# Install system dependencies including poppler-utils for pdf2image
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libpoppler-dev \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY app/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "500", "--reload"]
