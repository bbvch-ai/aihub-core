from typing import Annotated

from pydantic import BaseModel, Field


class AuthProviderResponse(BaseModel):
    """Represents a single identity provider available for login."""

    alias: Annotated[str, Field(description="Keycloak IDP alias used as kc_idp_hint parameter")]
    display_name: Annotated[str, Field(description="Human-readable name for the login button")]
    icon: Annotated[str, Field(description="PrimeIcon CSS class (e.g., pi-microsoft, pi-lock)")]
