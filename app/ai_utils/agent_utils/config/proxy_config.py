from dataclasses import dataclass
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

@dataclass
class OxylabsConfig:
    USERNAME = os.getenv("OXYLABS_USERNAME")
    PASSWORD = os.getenv("OXYLABS_PASSWORD")
    PROXY_HOST = os.getenv("OXYLABS_PROXY_HOST")
    PROXY_PORT = os.getenv("OXYLABS_PROXY_PORT")

    @classmethod
    def get_proxy_url(cls) -> str:
        return f"http://{cls.USERNAME}:{cls.PASSWORD}@{cls.PROXY_HOST}:{cls.PROXY_PORT}"

    @classmethod
    def get_proxies(cls) -> dict:
        proxy_url = cls.get_proxy_url()
        return {
            "http": proxy_url,
            "https": proxy_url
        } 