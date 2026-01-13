from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.routes.health.dto.HealthResponse import ApiHealthChecks, HealthResponse
from aihub_lib.routes.health.health_checks import check_milvus, check_mongodb, check_nats, check_redis, check_s3
from aihub_lib.routes.health.HealthController import HealthController
from fastapi import Request, Response
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE


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

    def get_ready(self, route: str = "/ready") -> "ApiHealthController":
        """Adds a readiness endpoint that checks all API dependencies."""

        @self.router.get(route, tags=self.tags)
        async def get_ready(request: Request, response: Response) -> HealthResponse:
            """
            Readiness check that verifies all API dependencies are available.
            Returns 200 if all checks pass, 503 if any check fails.
            """
            nc = getattr(request.app.state, "nc", None)
            redis = getattr(request.app.state, "redis", None)
            milvus_client = getattr(request.app.state, "milvus_client", None)
            s3_client = getattr(request.app.state, "s3_client", None)

            nats_healthy = await check_nats(nc)
            mongodb_healthy = check_mongodb()
            redis_healthy = await check_redis(redis)
            milvus_healthy = check_milvus(milvus_client)
            s3_healthy = check_s3(s3_client)

            all_healthy = nats_healthy and mongodb_healthy and redis_healthy and milvus_healthy and s3_healthy
            status = "ok" if all_healthy else "unhealthy"
            code = HTTP_200_OK if all_healthy else HTTP_503_SERVICE_UNAVAILABLE
            response.status_code = code

            return HealthResponse(
                status=status,
                code=code,
                checks=ApiHealthChecks(
                    nats=nats_healthy,
                    mongodb=mongodb_healthy,
                    redis=redis_healthy,
                    milvus=milvus_healthy,
                    s3=s3_healthy,
                ),
            )

        return self
