import asyncio
import time
import json
from pathlib import Path
from app.models.adapter.base import BaseProviderAdapter
from app.models.adapter.schemas import ModelRequest, ModelResponse

class DeterministicMockAdapter(BaseProviderAdapter):
    def __init__(self, simulate_timeout: bool = False, simulate_error: bool = False, delay: float = 0.1, fixture_path: str = None):
        self.simulate_timeout = simulate_timeout
        self.simulate_error = simulate_error
        self.delay = delay
        self.fixture_path = fixture_path

    async def generate(self, request: ModelRequest) -> ModelResponse:
        start_time = time.perf_counter()
        
        await asyncio.sleep(self.delay)

        latency = (time.perf_counter() - start_time) * 1000

        if self.simulate_timeout:
            return ModelResponse(
                content="",
                provider_name="mock",
                model_id="mock-model",
                latency_ms=latency,
                is_error=True,
                error_message="Provider timeout"
            )
            
        if self.simulate_error:
            return ModelResponse(
                content="",
                provider_name="mock",
                model_id="mock-model",
                latency_ms=latency,
                is_error=True,
                error_message="Invalid output schema returned by provider"
            )

        # Offline fallback: load pre-computed JSON fixture
        if self.fixture_path and Path(self.fixture_path).exists():
            with open(self.fixture_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            return ModelResponse(
                content=file_content,
                prompt_tokens=25,
                completion_tokens=len(file_content) // 4,
                provider_name="mock_offline",
                model_id="mock-offline-fixture",
                calculated_cost=0.0,
                latency_ms=latency
            )

        return ModelResponse(
            content='{"status": "success", "claim_id": "mock_123"}',
            prompt_tokens=25,
            completion_tokens=15,
            provider_name="mock",
            model_id="mock-model",
            calculated_cost=0.0,
            latency_ms=latency
        )