from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser

from swiss_ai_hub.api.routes.user.dto.dashboard.dashboard_dto import DashboardDTO
from swiss_ai_hub.api.routes.user.dto.minimal_user_dto import MinimalUserDTO


class UserDTO(MinimalUserDTO):
    dashboard: Annotated[DashboardDTO | None, Field(description="User dashboard configuration for index page")] = None
    roles: Annotated[list[str], Field(description="Roles the user holds in the current tenant.")] = []
    is_sys_admin: Annotated[
        bool, Field(description="Whether the user has the AIHubSysAdmin realm role in Keycloak.")
    ] = False

    @classmethod
    def from_keycloak_user_with_dashboard(
        cls,
        user: KeycloakUser,
        dashboard_dto: DashboardDTO | None = None,
        *,
        roles: list[str] | None = None,
        is_sys_admin: bool = False,
    ) -> Self:
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_image=None,
            dashboard=dashboard_dto,
            roles=roles or [],
            is_sys_admin=is_sys_admin,
        )
