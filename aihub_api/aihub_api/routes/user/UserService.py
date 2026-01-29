from typing import TYPE_CHECKING

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.auth.usage import UsageLimitService
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.user.UserEntity import Dashboard, DashboardItem, UserEntity
from mongoengine import DoesNotExist
from nats.aio.client import Client as NATS
from redis.asyncio import Redis

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.UsageStatusDTO import UsageStatusDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO
from aihub_api.routes.user.dto.UserWithAccessDTO import UserWithAccessDTO

if TYPE_CHECKING:
    from aihub_lib.runners.Runner import Runner


class UserService:
    """
    A service layer that encapsulates user-related logic:
    - Converting an authenticated user object to a UserDTO.
    - Retrieving user information from Azure AD or another identity provider.

    ### Why UserService?
    By separating user logic from controllers, the code remains organized and testable.
    `UserService`:
    - Uses `AzureIdentityProvider` to fetch user details by OID.
    - Converts `UserIdentity` objects into `UserDTO`s for consistent responses.

    ### Methods
    - `get_logged_in_user`: Converts the currently authenticated user into a `UserDTO`.
    - `get_user_by_oid`: Retrieves a user's info by their OID (Object ID), useful for
    building responses that include user details.
    """

    @staticmethod
    async def get_logged_in_user(user: UserIdentity, runner: "Runner", nc: NATS, t: LocaleHandler) -> UserWithAccessDTO:
        """
        Convert the `UserIdentity` (provided by the auth layer) into a UserDTO,
        including information from the UserEntity like dashboard settings, favorite modules, and roles.
        """
        return await UserService.get_user_with_access_by_oid(user.id, runner, nc, t)

    @staticmethod
    async def get_user_by_oid(user_oid: str) -> UserDTO:
        """
        Retrieve user info by OID (id, name, email, profile_image) as a UserDTO.
        It first checks a db (UserEntity). If recent and essential data is present,
        it's returned from the db. Otherwise, it fetches from the identity provider,
        ensures the UserEntity is created/updated (including roles and defaults for new users),
        and then returns basic info as a UserDTO.
        """
        user_entity = UserEntity.by_oid(user_oid)
        return UserDTO.from_user_entity(user_entity)

    @staticmethod
    async def get_user_with_access_by_oid(
        user_oid: str, runner: "Runner", nc: NATS, t: LocaleHandler
    ) -> UserWithAccessDTO:
        """
        Retrieve a user with their access rules (which services, agents, and processes they can access)
        """
        user_entity = UserEntity.by_oid(user_oid)
        return await UserWithAccessDTO.from_user_entity(user_entity, runner, nc, t)

    @staticmethod
    async def get_paginated_users(page: int = 1, page_size: int = 20) -> tuple[int, list[UserDTO]]:
        """
        Retrieves a paginated list of users from the local database.
        """
        skip = (page - 1) * page_size
        total = UserEntity.count_users()
        user_entities = UserEntity.get_paginated_users(skip=skip, limit=page_size)

        user_dtos = [UserDTO.from_user_entity(user) for user in user_entities]

        return total, user_dtos

    @staticmethod
    def get_user_dashboard(user: UserIdentity) -> DashboardDTO | None:
        """
        Retrieves the dashboard settings for the given authenticated user.
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
        Updates or creates the dashboard settings for the given authenticated user.
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

    @staticmethod
    async def get_user_usage(
        redis: Redis, user: UserIdentity, agent_path: str | None = None
    ) -> UsageStatusDTO:
        """Get the current usage status for the authenticated user."""
        status = await UsageLimitService.get_usage_status(redis, user.id, user.roles, agent_path=agent_path)
        return UsageStatusDTO.from_usage_status(status, agent_path=agent_path)
