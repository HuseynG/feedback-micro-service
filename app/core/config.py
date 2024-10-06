# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # Azure SQL Configuration
    AZURE_SQL_DRIVER: str = Field(default='ODBC Driver 18 for SQL Server', env='AZURE_SQL_DRIVER')
    AZURE_SQL_USERNAME: str = Field(..., env='AZURE_SQL_USERNAME')
    AZURE_SQL_PASSWORD: str = Field(..., env='AZURE_SQL_PASSWORD')
    AZURE_SQL_SERVER: str = Field(..., env='AZURE_SQL_SERVER')
    AZURE_SQL_PORT: str = Field(default='1433', env='AZURE_SQL_PORT')
    AZURE_SQL_DATABASE: str = Field(..., env='AZURE_SQL_DATABASE')
    AZURE_SQL_ENCRYPT: str = Field(default='yes', env='AZURE_SQL_ENCRYPT')
    AZURE_SQL_TRUST_CERTIFICATE: str = Field(default='no', env='AZURE_SQL_TRUST_CERTIFICATE')
    TIMEOUT: str = Field(default='30', env='TIMEOUT')
    
    # RabbitMQ Configuration
    RABBITMQ_HOST: str = Field(default='localhost', env='RABBITMQ_HOST')
    RABBITMQ_PORT: str = Field(default='5672', env='RABBITMQ_PORT')
    RABBITMQ_DEFAULT_USER: str = Field(default='guest', env='RABBITMQ_DEFAULT_USER')
    RABBITMQ_DEFAULT_PASS: str = Field(default='guest', env='RABBITMQ_DEFAULT_PASS')
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    @property
    def database_url(self) -> str:
        """
        Constructs the DATABASE_URL for Azure SQL using the provided environment variables.
        """
        driver_encoded = quote_plus(self.AZURE_SQL_DRIVER)
        password_encoded = quote_plus(self.AZURE_SQL_PASSWORD)
        return (
            f"mssql+pyodbc://{self.AZURE_SQL_USERNAME}:{password_encoded}"
            f"@{self.AZURE_SQL_SERVER}:{self.AZURE_SQL_PORT}/{self.AZURE_SQL_DATABASE}"
            f"?driver={driver_encoded}"
            f"&Encrypt={self.AZURE_SQL_ENCRYPT}"
            f"&TrustServerCertificate={self.AZURE_SQL_TRUST_CERTIFICATE}"
            f"&Connection Timeout={self.TIMEOUT}"
        )

settings = Settings()
