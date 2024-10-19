import hmac
import hashlib
import base64
from datetime import datetime, timezone

import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def generate_api_key(keyword: str, salt: str, timestamp: int) -> str:
    """
    Generates a base64 encoded API key using HMAC with SHA-256.
    """
    message = f"{keyword}:{timestamp}".encode('utf-8')
    hmac_key = hmac.new(salt.encode('utf-8'), message, hashlib.sha256).digest()
    return base64.b64encode(hmac_key).decode('utf-8')

# Example usage
# Get the current UTC time rounded down to the nearest hour (for testing purposes)
current_time = int(datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).timestamp())

# Generate the API key
api_key = generate_api_key(os.getenv("SECRET_KEYWORD"), os.getenv("SALT"), current_time)
print(api_key)
