from typing import TYPE_CHECKING

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.user.UserEntity import Dashboard, DashboardItem, UserEntity
from mongoengine import DoesNotExist
from nats.aio.client import Client as NATS

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.UserWithAccessDTO import UserWithAccessDTO

if TYPE_CHECKING:
    from aihub_lib.runners.Runner import Runner


class MyAccountService:
    """
    Service layer for personal account management operations.
    Handles the authenticated user's own profile, dashboard, and settings.
    """

    @staticmethod
    async def get_logged_in_user(user: UserIdentity, runner: "Runner", nc: NATS, t: LocaleHandler) -> UserWithAccessDTO:
        """
        Retrieve the currently logged-in user's info and access permissions.
        """
        user_entity = UserEntity.by_oid(user.id)
        return await UserWithAccessDTO.from_user_entity(user_entity, runner, nc, t)

    @staticmethod
    def get_user_dashboard(user: UserIdentity) -> DashboardDTO | None:
        """
        Retrieve the dashboard settings for the currently authenticated user.
        """
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
        """
        Update the dashboard settings for the currently authenticated user.
        """
        user_entity = UserEntity.by_oid(user.id)
        dashboard_data_dict = dashboard_dto.model_dump()

        children_data = dashboard_data_dict.pop("children", [])
        dashboard_items = []
        if children_data:
            for item_data in children_data:
                dashboard_items.append(DashboardItem(**item_data))

        user_entity.dashboard = Dashboard(children=dashboard_items, **dashboard_data_dict)
        user_entity.save()
