from typing import Annotated

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Annotated[str, Field(description="The health status of the application.")]
    code: Annotated[int, Field(description="HTTP status code.")]
    checks: Annotated[dict[str, bool] | None, Field(default=None, description="Individual health check results.")]
