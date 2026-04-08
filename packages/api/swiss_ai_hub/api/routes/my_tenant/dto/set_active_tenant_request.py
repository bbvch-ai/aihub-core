from typing import Annotated

from pydantic import BaseModel, Field


class SetActiveTenantRequest(BaseModel):
    """Request body for setting the active tenant."""

    tenant_id: Annotated[str, Field(description="The tenant ID to set as active")]
