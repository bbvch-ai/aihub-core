from contextlib import suppress

from fastapi import HTTPException, Request
from pymilvus import MilvusClient

from swiss_ai_hub.core.infrastructure.milvus.use_milvus import use_milvus


def use_optional_milvus(request: Request) -> MilvusClient | None:
    """Readiness variant of `use_milvus` that reports an unreachable Milvus as a missing client.

    Readiness exists to say which dependency is down, so it must not inherit the 503 `use_milvus`
    raises for callers: that would replace the whole report with a single error and hide the state
    of NATS, MongoDB, Redis and S3. Connecting through `use_milvus` keeps the reconnect behaviour,
    so a Milvus that came up after the API booted is reported ready.
    """
    with suppress(HTTPException):
        return use_milvus(request)
    return None
