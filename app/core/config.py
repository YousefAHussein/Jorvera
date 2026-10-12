from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model Configuration
    active_model_provider: str = "mock"
    openai_model_id: str = "gpt-4o-mini"
    google_model_id: str = "gemini-3.1-flash-lite"

    # Cost & Logging Ceilings
    model_timeout_seconds: int = 10
    max_monthly_budget_usd: float = 20.00
    enable_cost_logging: bool = True

settings = Settings()