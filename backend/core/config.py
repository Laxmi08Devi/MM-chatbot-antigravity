"""
Configuration management for the Multimodal AI Chatbot backend.
Uses pydantic-settings to load and validate environment variables from .env.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Multimodal AI Chatbot"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    BACKEND_URL: str = "http://127.0.0.1:8000"

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/multimodal_chatbot"
    SQLITE_FALLBACK_URL: str = "sqlite:///./chatbot_local.db"

    # AI Provider Selection: 'openai' or 'gemini'
    AI_PROVIDER: str = "openai"

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_IMAGE_MODEL: str = "dall-e-3"
    OPENAI_TTS_MODEL: str = "tts-1"
    OPENAI_WHISPER_MODEL: str = "whisper-1"

    # Gemini Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

    # Web Search (Tavily)
    TAVILY_API_KEY: Optional[str] = None

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    GENERATED_MEDIA_DIR: str = "./generated_media"
    MAX_UPLOAD_SIZE_MB: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_upload_path(self) -> Path:
        """Returns the uploads directory path and ensures it exists."""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_generated_media_path(self) -> Path:
        """Returns the generated media directory path and ensures it exists."""
        path = Path(self.GENERATED_MEDIA_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def has_openai(self) -> bool:
        """Check whether OpenAI API key is set."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.strip() and not self.OPENAI_API_KEY.startswith("your_"))

    @property
    def has_gemini(self) -> bool:
        """Check whether Gemini API key is set."""
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip() and not self.GEMINI_API_KEY.startswith("your_"))

    @property
    def has_tavily(self) -> bool:
        """Check whether Tavily API key is set."""
        return bool(self.TAVILY_API_KEY and self.TAVILY_API_KEY.strip() and not self.TAVILY_API_KEY.startswith("your_"))


settings = Settings()

