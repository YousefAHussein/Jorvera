from app.models.adapter.base import BaseProviderAdapter
from app.models.adapter.mock import DeterministicMockAdapter
from app.core.config import settings

def get_model_adapter(provider_name: str = None) -> BaseProviderAdapter:
    provider = provider_name or settings.active_model_provider
    
    if provider == "mock":
        return DeterministicMockAdapter()
    # elif provider == "openai":
    #     return OpenAIAdapter()

    raise ValueError(f"Unknown model provider configured: {provider}")