import logging

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.routes.health.dto.HealthResponse import HealthResponse
from aihub_lib.routes.health.HealthController import HealthController
from fastapi import Request, Response
from mongoengine.connection import get_connection
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

logger = logging.getLogger(__name__)


class ApiHealthController(HealthController):
    """
    API-specific health controller with liveness and readiness endpoints.

    Extends the base HealthController with a readiness check that verifies
    NATS, MongoDB, Redis, and Milvus connectivity.
    """

    def __init__(
        self, *, auth: AuthHandler, route: str = "/health", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_ready(self, route: str = "/ready") -> "ApiHealthController":
        """Adds a readiness endpoint that checks all API dependencies."""

        @self.router.get(route, tags=self.tags)
        async def get_ready(request: Request, response: Response) -> HealthResponse:
            """
            Readiness check that verifies all API dependencies are available.
            Returns 200 if all checks pass, 503 if any check fails.
            """
            nats_healthy = await _check_nats(request)
            mongodb_healthy = await _check_mongodb()
            redis_healthy = await _check_redis(request)
            milvus_healthy = _check_milvus(request)

            all_healthy = nats_healthy and mongodb_healthy and redis_healthy and milvus_healthy
            status = "ok" if all_healthy else "unhealthy"
            code = HTTP_200_OK if all_healthy else HTTP_503_SERVICE_UNAVAILABLE
            response.status_code = code

            return HealthResponse(
                status=status,
                code=code,
                checks={
                    "nats": nats_healthy,
                    "mongodb": mongodb_healthy,
                    "redis": redis_healthy,
                    "milvus": milvus_healthy,
                },
            )

        return self


async def _check_nats(request: Request) -> bool:
    """Check if NATS connection is healthy by flushing (sends PING, waits for PONG)."""
    if not hasattr(request.app.state, "nc"):
        return False
    nc = request.app.state.nc
    if nc is None:
        return False
    try:
        await nc.flush(timeout=5)
        return True
    except Exception as e:
        logger.debug(f"NATS health check failed: {e}")
        return False


async def _check_mongodb() -> bool:
    """Check if MongoDB connection is available."""
    try:
        conn = get_connection()
        conn.admin.command("ping")
        return True
    except Exception as e:
        logger.debug(f"MongoDB health check failed: {e}")
        return False


async def _check_redis(request: Request) -> bool:
    """Check if Redis connection is healthy by pinging."""
    if not hasattr(request.app.state, "redis"):
        return False
    redis = request.app.state.redis
    if redis is None:
        return False
    try:
        await redis.ping()
        return True
    except Exception as e:
        logger.debug(f"Redis health check failed: {e}")
        return False


def _check_milvus(request: Request) -> bool:
    """Check if Milvus connection is healthy by listing collections."""
    if not hasattr(request.app.state, "milvus_client"):
        return False
    milvus_client = request.app.state.milvus_client
    if milvus_client is None:
        return False
    try:
        # list_collections is a lightweight operation to verify connectivity
        milvus_client.list_collections()
        return True
    except Exception as e:
        logger.debug(f"Milvus health check failed: {e}")
        return False
