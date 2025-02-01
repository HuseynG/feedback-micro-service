import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.exceptions import HTTPException
from mongomock import MongoClient

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test_key',
        'AZURE_OPENAI_BASE_API_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_API_VERSION': '2024-02-15',
        'GOOGLE_API_KEY': 'test_google_key',
        'EXPECTED_API_KEY': 'test-key',  # Add this for API key validation
        'API_KEY': 'test-key'
    }):
        yield

# Create a more complete mock of google.genai
mock_types = MagicMock()
mock_types.Tool = MagicMock()
mock_types.GenerateContentConfig = MagicMock()
mock_types.GoogleSearch = MagicMock()

mock_genai = MagicMock()
mock_genai.types = mock_types
mock_genai.GenerativeModel = MagicMock()

# Mock the entire google hierarchy
sys.modules['google'] = MagicMock()
sys.modules['google.genai'] = mock_genai
sys.modules['google.genai.types'] = mock_types

# Add the parent folder (app) to the PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from main import app
from typing import Generator

@pytest.fixture
def test_client() -> Generator:
    app.mongodb_client = MongoClient()
    app.database = app.mongodb_client.test_db
    
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_db():
    return MongoClient().test_db 

# Mock the API key validation
async def mock_verify_api_key(request: Request) -> bool:
    api_key = request.headers.get('x-api-key')
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key is required")
    return True

@pytest.fixture(autouse=True)
def mock_api_key_validation():
    with patch('app.utils.auth.verify_api_key', mock_verify_api_key):
        yield 