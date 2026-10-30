import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from swiss_ai_hub.api.request_limits import JsonBodySizeLimitMiddleware

LIMIT = 100


@pytest.fixture
def client() -> AsyncClient:
    app = FastAPI()
    app.add_middleware(JsonBodySizeLimitMiddleware, max_bytes=LIMIT)

    @app.post("/json")
    async def echo_json(body: dict) -> dict:
        return {"keys": len(body)}

    @app.post("/raw")
    async def echo_raw(request: Request) -> dict:
        return {"length": len(await request.body())}

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_accepts_a_body_within_the_limit(client: AsyncClient):
    response = await client.post("/json", json={"a": "b"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rejects_a_declared_length_over_the_limit(client: AsyncClient):
    response = await client.post("/json", json={"a": "x" * LIMIT})
    assert response.status_code == 413
    assert str(LIMIT) in response.json()["detail"]


@pytest.mark.asyncio
async def test_rejects_a_chunked_body_over_the_limit(client: AsyncClient):
    async def chunks():
        yield b'{"a": "'
        yield b"x" * LIMIT
        yield b'"}'

    response = await client.post("/json", content=chunks(), headers={"Content-Type": "application/json"})
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_leaves_other_bodies_to_their_endpoints(client: AsyncClient):
    response = await client.post(
        "/raw", content=b"x" * (LIMIT * 2), headers={"Content-Type": "application/octet-stream"}
    )
    assert response.status_code == 200
    assert response.json() == {"length": LIMIT * 2}
