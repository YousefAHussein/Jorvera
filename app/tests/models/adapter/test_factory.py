import pytest
from app.models.adapter.factory import get_model_adapter
from app.models.adapter.mock import DeterministicMockAdapter

def test_get_mock_adapter():
    adapter = get_model_adapter("mock")
    assert isinstance(adapter, DeterministicMockAdapter)

def test_get_unknown_adapter_raises_error():
    with pytest.raises(ValueError, match="Unknown model provider"):
        get_model_adapter("unsupported_provider")