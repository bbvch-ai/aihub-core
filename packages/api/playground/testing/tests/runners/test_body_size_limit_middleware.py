import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from swiss_ai_hub.api.request_limits import BodySizeLimitMiddleware

LIMIT = 100
EXEMPT = "/parsing/process"


@pytest.fixture
def client() -> AsyncClient:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=LIMIT, exempt_path_suffixes=(EXEMPT,))

    @app.post("/json")
    async def echo_json(body: dict) -> dict:
        return {"keys": len(body)}

    @app.post("/raw")
    async def echo_raw(request: Request) -> dict:
        return {"length": len(await request.body())}

    @app.put(EXEMPT)
    async def streamed(request: Request) -> dict:
        return {"length": len(await request.body())}

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_accepts_a_body_within_the_limit(client: AsyncClient):
    assert (await client.post("/json", json={"a": "b"})).status_code == 200


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
@pytest.mark.parametrize("headers", [{}, {"Content-Type": "text/plain"}, {"Content-Type": "application/octet-stream"}])
async def test_a_body_of_any_other_type_or_none_is_bounded_too(client: AsyncClient, headers: dict):
    async def chunks():
        yield b"x" * (LIMIT * 2)

    response = await client.post("/raw", content=chunks(), headers=headers)
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_multipart_uploads_and_exempt_paths_bound_themselves(client: AsyncClient):
    upload = await client.post("/raw", files={"file": ("a.bin", b"x" * (LIMIT * 2))})
    streamed = await client.put(EXEMPT, content=b"x" * (LIMIT * 2), headers={"Content-Type": "application/pdf"})

    assert upload.status_code == 200
    assert streamed.status_code == 200
    assert streamed.json() == {"length": LIMIT * 2}
