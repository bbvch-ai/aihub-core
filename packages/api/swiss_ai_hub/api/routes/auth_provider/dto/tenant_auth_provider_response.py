from typing import Annotated

from pydantic import BaseModel, Field


class TenantAuthProviderResponse(BaseModel):
    """Unknown and unlisted tenants both get a null alias, so the answer never reveals whether a tenant exists."""

    alias: Annotated[
        str | None,
        Field(description="Keycloak IDP alias to start the tenant's login with, or null when it has no login link"),
    ]
