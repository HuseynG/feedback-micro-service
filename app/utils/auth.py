import hmac
import hashlib
import base64
from fastapi import FastAPI, Header, HTTPException, Depends
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

SECRET_KEYWORD = os.getenv("SECRET_KEYWORD")
SALT = os.getenv("SALT")

def verify_api_key(api_key: str = Header(...)) -> None:
    """
    Verifies the API key by checking if it matches the expected key.
    The API key is generated using the keyword, salt, and current UTC time rounded to the nearest hour.
    """
    try:
        # Decode the provided API key from base64
        decoded_key = base64.b64decode(api_key.encode('utf-8'))

        # Get the current UTC time rounded down to the nearest hour (in seconds)
        current_time = int(datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).timestamp())

        # Check within the current hour and the previous hour
        for timestamp in [current_time, current_time - 3600]:
            expected_key = hmac.new(
                SALT.encode('utf-8'),
                f"{SECRET_KEYWORD}:{timestamp}".encode('utf-8'),
                hashlib.sha256
            ).digest()

            # Compare the provided key with the expected one
            if hmac.compare_digest(decoded_key, expected_key):
                return  # Valid API key, exit the function

        # If no match found within the valid time window
        raise HTTPException(status_code=403, detail="Invalid API Key")

    except Exception as e:
        raise HTTPException(status_code=403, detail="Invalid API Key")
