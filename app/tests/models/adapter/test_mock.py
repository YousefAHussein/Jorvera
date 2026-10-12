import pytest
import json
from app.models.adapter.mock import DeterministicMockAdapter
from app.models.adapter.schemas import ModelRequest, ModelMessage

@pytest.fixture
def sample_request():
    return ModelRequest(messages=[ModelMessage(role="user", content="Test")])

@pytest.mark.asyncio
async def test_mock_adapter_success(sample_request):
    # Pass a small delay to guarantee latency_ms > 0
    adapter = DeterministicMockAdapter(delay=0.01)
    response = await adapter.generate(sample_request)

    assert response.is_error is False
    assert response.provider_name == "mock"
    assert response.model_id == "mock-model"
    assert response.calculated_cost == 0.0
    assert response.latency_ms > 0
    assert "success" in response.content

@pytest.mark.asyncio
async def test_mock_adapter_timeout(sample_request):
    adapter = DeterministicMockAdapter(simulate_timeout=True, delay=0.01)
    response = await adapter.generate(sample_request)

    assert response.is_error is True
    assert response.error_message == "Provider timeout"
    assert response.model_id == "mock-model"
    assert response.latency_ms > 0

@pytest.mark.asyncio
async def test_mock_adapter_invalid_output(sample_request):
    adapter = DeterministicMockAdapter(simulate_error=True, delay=0.01)
    response = await adapter.generate(sample_request)

    assert response.is_error is True
    assert response.error_message == "Invalid output schema returned by provider"
    assert response.model_id == "mock-model"
    assert response.latency_ms > 0


@pytest.mark.asyncio
async def test_mock_adapter_offline_fallback(sample_request, tmp_path):
    # Create a temporary JSON fixture file for the test
    fixture_data = {"status": "offline_success", "claim_id": "fallback_999"}
    fixture_file = tmp_path / "fallback.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")

    # Initialize adapter with the fixture path
    adapter = DeterministicMockAdapter(fixture_path=str(fixture_file), delay=0.01)
    response = await adapter.generate(sample_request)

    assert response.is_error is False
    assert response.provider_name == "mock_offline"
    assert response.model_id == "mock-offline-fixture"
    assert "fallback_999" in response.content