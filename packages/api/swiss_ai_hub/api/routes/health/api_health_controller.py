import asyncio
from typing import Annotated, Self

from fastapi import Depends, Response
from nats.aio.client import Client as NATS
from pymilvus import MilvusClient
from redis.asyncio import Redis
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.dependencies import use_nats
from swiss_ai_hub.core.infrastructure import use_milvus, use_redis, use_s3
from swiss_ai_hub.core.routes import (
    ApiHealthChecks,
    HealthController,
    HealthResponse,
    check_milvus,
    check_mongodb,
    check_nats,
    check_redis,
    check_s3,
)


class ApiHealthController(HealthController):
    """
    API-specific health controller with liveness and readiness endpoints.

    Extends the base HealthController with a readiness check that verifies
    NATS, MongoDB, Redis, Milvus, and S3 connectivity.
    """

    def __init__(
        self, *, auth: AuthHandler, route: str = "/health", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_ready(self, route: str = "/ready") -> Self:
        """Adds a readiness endpoint that checks all API dependencies."""

        @self.router.get(route, tags=self.tags)
        async def get_ready(
            response: Response,
            nc: Annotated[NATS, Depends(use_nats)],
            redis: Annotated[Redis, Depends(use_redis)],
            milvus_client: Annotated[MilvusClient, Depends(use_milvus)],
            s3_client: Annotated[object, Depends(use_s3)],
        ) -> HealthResponse:
            """
            Readiness check that verifies all API dependencies are available.
            Returns 200 if all checks pass, 503 if any check fails.
            """
            nats_healthy, mongodb_healthy, redis_healthy, milvus_healthy, s3_healthy = await asyncio.gather(
                check_nats(nc),
                asyncio.to_thread(check_mongodb),
                check_redis(redis),
                asyncio.to_thread(check_milvus, milvus_client),
                asyncio.to_thread(check_s3, s3_client),
            )

            all_healthy = nats_healthy and mongodb_healthy and redis_healthy and milvus_healthy and s3_healthy
            status = "ok" if all_healthy else "unhealthy"
            code = HTTP_200_OK if all_healthy else HTTP_503_SERVICE_UNAVAILABLE
            response.status_code = code

            return HealthResponse(
                status=status,
                code=code,
                version=self._version,
                checks=ApiHealthChecks(
                    nats=nats_healthy,
                    mongodb=mongodb_healthy,
                    redis=redis_healthy,
                    milvus=milvus_healthy,
                    s3=s3_healthy,
                ),
            )

        return self
