

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    APP_NAME: str = "Personal AI Assistant"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"

    # AI provider configuration
    AI_PROVIDER: str = "groq"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    # AI generation limits
    AI_MAX_OUTPUT_TOKENS: int = 1024

    # Groq API quota limits
    GROQ_RPM_LIMIT: int = 30
    GROQ_RPD_LIMIT: int = 1000
    GROQ_TPM_LIMIT: int = 8000
    GROQ_TPD_LIMIT: int = 200000

    # Block AI requests at 90% of configured quota
    AI_QUOTA_THRESHOLD: float = 0.90

    DATABASE_URL: str = ""
        # Authentication and session security
    SESSION_TTL_HOURS: int = 12

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application configuration."""

    return Settings()


settings = get_settings()
