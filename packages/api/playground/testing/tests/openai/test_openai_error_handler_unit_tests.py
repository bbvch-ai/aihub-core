import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from swiss_ai_hub.api.routes.openai.openai_error_handler import OpenaiErrorHandler


class Body(BaseModel):
    model: str


@pytest.fixture
def client() -> AsyncClient:
    app = FastAPI()
    OpenaiErrorHandler.register(app)

    @app.post("/api/v1/active/openai/chat/completions")
    async def completions(body: Body) -> dict:
        raise HTTPException(status_code=404, detail=f"Model {body.model} not found.")

    @app.post("/api/v1/active/agents/something")
    async def other(body: Body) -> dict:
        raise HTTPException(status_code=404, detail="Nothing here.")

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_an_openai_route_error_carries_the_openai_error_object_and_detail(client: AsyncClient):
    response = await client.post("/api/v1/active/openai/chat/completions", json={"model": "gpt-4o"})

    assert response.status_code == 404
    assert response.json()["error"] == {
        "message": "Model gpt-4o not found.",
        "type": "not_found_error",
        "param": None,
        "code": 404,
    }
    assert response.json()["detail"] == "Model gpt-4o not found."


@pytest.mark.asyncio
async def test_an_invalid_openai_request_is_a_400_naming_the_field(client: AsyncClient):
    response = await client.post("/api/v1/active/openai/chat/completions", json={})

    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_request_error"
    assert response.json()["error"]["param"] == "model"
    assert isinstance(response.json()["detail"], list)


@pytest.mark.asyncio
async def test_other_routes_keep_fastapis_responses(client: AsyncClient):
    assert (await client.post("/api/v1/active/agents/something", json={})).status_code == 422
    not_found = await client.post("/api/v1/active/agents/something", json={"model": "x"})
    assert not_found.json() == {"detail": "Nothing here."}


@pytest.mark.asyncio
async def test_a_structured_detail_is_kept_and_its_message_used():
    app = FastAPI()
    OpenaiErrorHandler.register(app)

    @app.post("/api/v1/active/openai/chat/completions")
    async def limited() -> dict:
        raise HTTPException(status_code=429, detail={"message": "Usage limit reached.", "resets_at": "tomorrow"})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/active/openai/chat/completions")

    assert response.json()["detail"] == {"message": "Usage limit reached.", "resets_at": "tomorrow"}
    assert response.json()["error"]["message"] == "Usage limit reached."
    assert response.json()["error"]["type"] == "rate_limit_error"
