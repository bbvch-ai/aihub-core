import logging

from fastapi import HTTPException, Request
from pymilvus import MilvusClient
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings

logger = logging.getLogger(__name__)


def use_milvus(request: Request) -> MilvusClient:
    """FastAPI dependency that provides the Milvus client from app state.

    The client is built here rather than only at startup so a Milvus that was unreachable when the
    process booted is picked up by the next request instead of staying broken until a restart. A
    failed connection is therefore a 503 on one request, never a dead process — see the note in
    `lifetime_manager` for the crash loop this replaces.
    """
    if request.app.state.milvus_client is None:
        milvus_settings = MilvusSettings()
        try:
            request.app.state.milvus_client = MilvusClient(uri=milvus_settings.URL, token=milvus_settings.get_token())
        # Broad on purpose: pymilvus re-raises the codes in its own IGNORE_RETRY_CODES as bare
        # grpc.RpcError instead of MilvusException, so naming MilvusException would let an
        # UNAUTHENTICATED from a token mismatch escape as a 500.
        except Exception as milvus_unreachable_exception:
            logger.warning(f"Milvus is unreachable: {milvus_unreachable_exception}")
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE, detail="Vector store is temporarily unavailable."
            ) from milvus_unreachable_exception

    return request.app.state.milvus_client
