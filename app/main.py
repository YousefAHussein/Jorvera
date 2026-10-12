from fastapi import FastAPI, Depends
from app.models.adapter.schemas import ModelRequest, ModelResponse
from app.models.adapter.base import BaseProviderAdapter
from app.api.dependencies import get_current_model_adapter

app = FastAPI(title="Model Adapter Skeleton S0-05")

@app.post("/generate", response_model=ModelResponse)
async def generate_text(
    request: ModelRequest,
    adapter: BaseProviderAdapter = Depends(get_current_model_adapter)
):
    return await adapter.generate(request)