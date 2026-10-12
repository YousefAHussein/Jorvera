from fastapi import Depends
from app.models.adapter.base import BaseProviderAdapter
from app.models.adapter.factory import get_model_adapter

def get_current_model_adapter() -> BaseProviderAdapter:
    """FastAPI dependency to inject the active model adapter into route handlers."""
    return get_model_adapter()