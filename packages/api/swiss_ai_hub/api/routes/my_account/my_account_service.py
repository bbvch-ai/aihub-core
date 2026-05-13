from typing import TYPE_CHECKING

from fastapi import HTTPException
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.user.user_dashboard_entity import Dashboard, DashboardItem, UserDashboardEntity

from swiss_ai_hub.api.routes.user.dto.dashboard.dashboard_dto import DashboardDTO
from swiss_ai_hub.api.routes.user.dto.user_with_access_dto import UserWithAccessDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners import Runner


class MyAccountService:
    """Handles account-level operations for the logged-in user."""

    @staticmethod
    async def get_my_account(user: UserIdentity, runner: "Runner", nc: NATS, t: LocaleHandler) -> UserWithAccessDTO:
        """Converts the authenticated user's identity into a full profile DTO."""
        return await UserWithAccessDTO.from_user_identity(user, user.acting_within_tenant, runner, nc, t)

    @staticmethod
    def get_user_dashboard(user: UserIdentity) -> DashboardDTO | None:
        """Retrieves the dashboard settings for the authenticated user."""
        dashboard = UserDashboardEntity.get_dashboard(user.id)
        if dashboard:
            dashboard_data = dashboard.to_mongo()
            return DashboardDTO(**dashboard_data)
        return None

    @staticmethod
    async def update_user_dashboard(user: UserIdentity, dashboard_dto: DashboardDTO) -> None:
        """Updates or creates the dashboard settings for the authenticated user."""
        dashboard_data_dict = dashboard_dto.model_dump()

        children_data = dashboard_data_dict.pop("children", [])
        dashboard_items = [DashboardItem(**item_data) for item_data in children_data]

        dashboard = Dashboard(children=dashboard_items, **dashboard_data_dict)
        UserDashboardEntity.set_dashboard(user.id, dashboard)

    @staticmethod
    async def update_user_locale(user: UserIdentity, locale: str) -> None:
        """Persists the user's preferred UI language as a Keycloak attribute."""
        if locale not in LocaleHandler.LOCALE_WHITE_LIST:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported locale '{locale}'. Allowed: {LocaleHandler.LOCALE_WHITE_LIST}",
            )
        await KeycloakAdminService.set_preferred_locale(user.id, locale)
