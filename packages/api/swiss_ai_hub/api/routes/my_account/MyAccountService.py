from typing import TYPE_CHECKING

from mongoengine import DoesNotExist
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.persistence.user.UserEntity import Dashboard, DashboardItem, UserEntity

from swiss_ai_hub.api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from swiss_ai_hub.api.routes.user.dto.UserWithAccessDTO import UserWithAccessDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners.Runner import Runner


class MyAccountService:
    """Handles account-level operations for the logged-in user."""

    @staticmethod
    async def get_my_account(user: UserIdentity, runner: "Runner", nc: NATS, t: LocaleHandler) -> UserWithAccessDTO:
        """Converts the authenticated user's identity into a full profile DTO."""
        user_entity = UserEntity.by_oid(user.id)
        return await UserWithAccessDTO.from_user_entity(user_entity, user.acting_within_tenant, runner, nc, t)

    @staticmethod
    def get_user_dashboard(user: UserIdentity) -> DashboardDTO | None:
        """Retrieves the dashboard settings for the authenticated user."""
        try:
            user_entity = UserEntity.by_oid(user.id)
        except DoesNotExist:
            return None

        if user_entity.dashboard:
            dashboard_data = user_entity.dashboard.to_mongo()
            return DashboardDTO(**dashboard_data)
        return None

    @staticmethod
    async def update_user_dashboard(user: UserIdentity, dashboard_dto: DashboardDTO) -> None:
        """Updates or creates the dashboard settings for the authenticated user."""
        user_entity = UserEntity.by_oid(user.id)
        dashboard_data_dict = dashboard_dto.model_dump()

        children_data = dashboard_data_dict.pop("children", [])
        dashboard_items = []
        if children_data:
            for item_data in children_data:
                dashboard_items.append(DashboardItem(**item_data))

        user_entity.dashboard = Dashboard(children=dashboard_items, **dashboard_data_dict)
        user_entity.save()
