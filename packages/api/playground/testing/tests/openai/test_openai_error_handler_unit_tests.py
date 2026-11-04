import json

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from swiss_ai_hub.api.request_limits import BodySizeLimitMiddleware
from swiss_ai_hub.api.routes.openai.openai_error_handler import OpenaiErrorHandler

LIMIT = 100


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


@pytest.mark.asyncio
async def test_a_routing_error_from_starlette_carries_the_openai_error_object(client: AsyncClient):
    response = await client.get("/api/v1/active/openai/chat/completions")

    assert response.status_code == 405
    assert response.json()["error"]["message"] == "Method Not Allowed"


@pytest.mark.asyncio
async def test_a_request_the_platform_refuses_as_unprocessable_is_a_400():
    app = FastAPI()
    OpenaiErrorHandler.register(app)

    @app.post("/api/v1/active/openai/chat/completions")
    async def invalid_file() -> dict:
        raise HTTPException(status_code=422, detail="The content of 'a.txt' is not valid base64.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/active/openai/chat/completions")

    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_request_error"
    assert response.json()["error"]["message"] == "The content of 'a.txt' is not valid base64."


@pytest.mark.asyncio
@pytest.mark.parametrize("chunked", [False, True])
async def test_a_body_over_the_limit_is_refused_in_the_openai_format(chunked: bool):
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=LIMIT)
    OpenaiErrorHandler.register(app)

    @app.post("/api/v1/active/openai/chat/completions")
    async def completions(body: Body) -> dict:
        return {"model": body.model}

    @app.post("/api/v1/active/agents/something")
    async def other(body: Body) -> dict:
        return {"model": body.model}

    payload = json.dumps({"model": "x" * LIMIT}).encode()

    async def chunks():
        yield payload

    content = chunks() if chunked else payload
    headers = {"Content-Type": "application/json"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        openai = await client.post("/api/v1/active/openai/chat/completions", content=content, headers=headers)
        content = chunks() if chunked else payload
        other = await client.post("/api/v1/active/agents/something", content=content, headers=headers)

    assert openai.status_code == 413
    assert openai.json()["error"]["type"] == "invalid_request_error"
    assert str(LIMIT) in openai.json()["error"]["message"]
    assert other.status_code == 413
    assert "error" not in other.json()
