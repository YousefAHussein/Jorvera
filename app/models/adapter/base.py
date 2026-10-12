from abc import ABC, abstractmethod
from app.models.adapter.schemas import ModelRequest, ModelResponse

class BaseProviderAdapter(ABC):
    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """
        Executes the model request and returns a standard ModelResponse.
        Must handle timeouts and invalid outputs gracefully.
        """
        pass