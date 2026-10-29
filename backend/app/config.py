from pathlib import Path
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Project root: /Users/oishikdalui/Documents/windowshared/corporate-financial-health
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
ENV_PATH = PROJECT_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings(BaseModel):
    """Application and Database Configuration Settings."""

    app_name: str = "Corporate Financial Health AI Assistant"
    app_version: str = "1.0.0"
    debug: bool = False

    # MySQL Configuration
    db_host: str = Field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    db_port: int = Field(default_factory=lambda: int(os.getenv("DB_PORT", "3306")))
    db_name: str = Field(default_factory=lambda: os.getenv("DB_NAME", "corporate_financial_health"))
    db_user: str = Field(default_factory=lambda: os.getenv("DB_USER", "root"))
    db_password: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))

    # AI Configuration (OpenAI or compatible provider)
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model_sql: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_SQL", "gpt-4o"))
    openai_model_insight: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_INSIGHT", "gpt-4o-mini"))

    # Cache & Rate Limiting
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    jwt_secret_key: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "super-secret-key-production"))
    api_rate_limit: int = Field(default_factory=lambda: int(os.getenv("API_RATE_LIMIT", "30")))


settings = Settings()
