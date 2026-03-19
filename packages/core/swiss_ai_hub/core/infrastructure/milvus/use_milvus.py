from fastapi import Request
from pymilvus import MilvusClient


def use_milvus(request: Request) -> MilvusClient:
    """FastAPI dependency that provides the Milvus client from app state."""
    return request.app.state.milvus_client
