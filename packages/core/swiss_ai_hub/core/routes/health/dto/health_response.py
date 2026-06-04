from typing import Annotated

from pydantic import BaseModel, Field


class ApiHealthChecks(BaseModel):
    """Health check results for API service dependencies."""

    nats: Annotated[bool, Field(description="NATS message broker connectivity.")]
    mongodb: Annotated[bool, Field(description="MongoDB database connectivity.")]
    redis: Annotated[bool, Field(description="Redis/Valkey cache connectivity.")]
    milvus: Annotated[bool, Field(description="Milvus vector database connectivity.")]
    s3: Annotated[bool, Field(description="S3/SeaweedFS object storage connectivity.")]


class AgentHealthChecks(BaseModel):
    """Health check results for Agent service dependencies."""

    running: Annotated[bool, Field(description="Whether the agent runner is running.")]
    nats: Annotated[bool, Field(description="NATS message broker connectivity.")]
    redis: Annotated[bool, Field(description="Redis/Valkey cache connectivity.")]
    milvus: Annotated[bool, Field(description="Milvus vector database connectivity.")]


class ProcessHealthChecks(BaseModel):
    """Health check results for Process service dependencies."""

    running: Annotated[bool, Field(description="Whether the process runner is running.")]
    nats: Annotated[bool, Field(description="NATS message broker connectivity.")]
    redis: Annotated[bool, Field(description="Redis/Valkey cache connectivity.")]


class HealthResponse(BaseModel):
    """Standard health check response."""

    status: Annotated[str, Field(description="The health status of the application.")]
    code: Annotated[int, Field(description="HTTP status code.")]
    version: Annotated[str | None, Field(default=None, description="Running service version.")]
    checks: Annotated[
        ApiHealthChecks | AgentHealthChecks | ProcessHealthChecks | None,
        Field(default=None, description="Individual health check results."),
    ]
