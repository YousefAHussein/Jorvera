from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ModelMessage(BaseModel):
    role: str = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")

class ModelRequest(BaseModel):
    messages: List[ModelMessage]
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None
    response_schema: Optional[Dict[str, Any]] = None

class ModelResponse(BaseModel):
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    provider_name: str
    model_id: Optional[str] = None
    calculated_cost: float = 0.0
    latency_ms: float = 0.0
    is_error: bool = False
    error_message: Optional[str] = None