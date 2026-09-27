from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "ATHENEUS Corporate Verification Engine"
    API_V1_STR: str = "/api/v1"
    
    # External API Keys
    TAVILY_API_KEY: str
    GROQ_API_KEY: str
    
    # Request Defaults
    DEFAULT_MAX_SEARCH_RESULTS: int = 5
    REQUEST_TIMEOUT_SECONDS: float = 15.0

    # Pydantic Settings Config: reads automatically from local .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate a singleton settings instance
settings = Settings()