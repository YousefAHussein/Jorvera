from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Model configuration (existing S0-05 work)
    active_model_provider: str = "mock"
    openai_model_id: str = "gpt-4o-mini"
    google_model_id: str = "gemini-3.1-flash-lite"

    # Cost and logging ceilings (existing S0-05 work)
    model_timeout_seconds: int = 10
    max_monthly_budget_usd: float = 20.00
    enable_cost_logging: bool = True

    # Database configuration (S0-04)
    # DATABASE_URL may use Neon's pooled endpoint for normal application traffic.
    database_url: str | None = None
    # Prefer Neon's direct (non-pooler) URL for Alembic migrations and smoke tests.
    database_url_direct: str | None = None
    database_echo: bool = False
    database_connect_timeout_seconds: int = 10


settings = Settings()
