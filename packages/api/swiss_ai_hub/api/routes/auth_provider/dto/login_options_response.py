from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.auth_provider.dto.auth_provider_response import AuthProviderResponse


class LoginOptionsResponse(BaseModel):
    """What the generic login page may offer. A welcome-page instance never lists a federated provider here."""

    welcome_page: Annotated[
        bool,
        Field(description="Show a welcome page pointing to the organisation's login link instead of provider buttons"),
    ]
    providers: Annotated[
        list[AuthProviderResponse],
        Field(
            description="Providers to offer as login buttons; on a welcome-page instance at most the direct Keycloak "
            "login, which administrators use"
        ),
    ]
