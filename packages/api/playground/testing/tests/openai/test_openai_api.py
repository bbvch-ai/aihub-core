import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_handler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.testing import mock_role_entity_methods
from swiss_ai_hub.core.testing import mock_tenant_entity_autouse
from swiss_ai_hub.core.testing import mock_user_entity_autouse

from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_URL = "http://test"
MODELS_ENDPOINT = "/api/v1/openai/models"
CHAT_MODEL = "text-generation/gpt-oss-120b"
EMBEDDING_MODEL = "embedding/bge-m3"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client():
    """Create an API client with OpenaiController endpoints mounted."""
    auth = DangerousDevelopmentOnlyAuthHandler()
    controller = OpenaiController(auth=auth).get_models().get_model().get_embeddings().chat_completion()
    runner = ApiTestRunner()
    runner.mount(controller)
    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio(loop_scope="module")
async def test_get_models(api_client):
    """Test GET /openai/models returns a valid model list."""
    response = await api_client.get(MODELS_ENDPOINT)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data.get("object") == "list"
    assert isinstance(data.get("data"), list)
    model_ids = [model.get("id") for model in data.get("data")]
    assert CHAT_MODEL in model_ids


@pytest.mark.asyncio(loop_scope="module")
async def test_get_model(api_client):
    """Test GET /openai/models/{full_path} returns valid model details."""
    response = await api_client.get(f"{MODELS_ENDPOINT}/{CHAT_MODEL}")
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data.get("id") == CHAT_MODEL
    assert data.get("object") == "model"
    assert isinstance(data.get("created"), int)
    assert data.get("owned_by") == "aihub"


@pytest.mark.asyncio(loop_scope="module")
async def test_get_embeddings(api_client):
    """Test POST /openai/embeddings returns valid embeddings."""
    payload = {
        "input": "Test input for embeddings",
        "model": EMBEDDING_MODEL,
        "encoding_format": "float",
    }
    response = await api_client.post("/api/v1/openai/embeddings", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data.get("object") == "list"
    assert data.get("model") == EMBEDDING_MODEL
    assert isinstance(data.get("data"), list)
    for item in data.get("data"):
        assert item.get("object") == "embeddings"
        assert isinstance(item.get("embedding"), list)
        assert isinstance(item.get("index"), int)


@pytest.mark.asyncio(loop_scope="module")
async def test_chat_completion(api_client):
    """Test POST /openai/chat/completions returns a valid chat completion."""
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "user", "content": "Say: Hello"},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "Again"},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "Again"},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "Again"},
        ],
        "temperature": 0,
        "stream": False,
    }
    response = await api_client.post("/api/v1/openai/chat/completions", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert "id" in data
    assert "object" in data
    assert "choices" in data
    assert isinstance(data["choices"], list)
    completion = data["choices"][0]["message"]
    assert completion.get("role") == "assistant"
    assert "hello" in completion.get("content").lower()
