from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity


class UserIdentity(BaseModel):
    """Lightweight identity object for authenticated users."""

    id: Annotated[str, Field(description="The unique identifier for the user.")]
    name: Annotated[str, Field(description="The name of the user.")]
    email: Annotated[str, Field(description="The email address of the user.")]
    roles: Annotated[list[str], Field(description="The roles assigned to the user within the acting tenant.")]
    acting_within_tenant: Annotated[
        TenantIdentity, Field(description="The tenant context the user is operating within.")
    ]
