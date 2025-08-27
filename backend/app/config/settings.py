from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8003"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "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")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-5-chat")
    
    # Frankfurter API Configuration
    FRANKFURTER_BASE_URL: str = os.getenv("FRANKFURTER_BASE_URL", "https://api.frankfurter.app/latest?amount=100&from=USD&to=EUR")
    
    # LLM Configuration
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "500"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    
    # Session Configuration
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    MAX_CONVERSATION_LENGTH: int = int(os.getenv("MAX_CONVERSATION_LENGTH", "20"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()