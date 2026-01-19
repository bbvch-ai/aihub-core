from typing import TYPE_CHECKING

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.user.UserEntity import UserEntity
from nats.aio.client import Client as NATS

from aihub_api.routes.user.dto.UserDTO import UserDTO
from aihub_api.routes.user.dto.UserWithAccessDTO import UserWithAccessDTO

if TYPE_CHECKING:
    from aihub_lib.runners.Runner import Runner


class UserService:
    """
    Service layer for user administration operations.

    Provides methods for administrators to retrieve and manage users.
    For personal account operations, see MyAccountService.
    """

    @staticmethod
    async def get_user_by_oid(user_oid: str) -> UserDTO:
        """
        Retrieve user info by OID as a UserDTO.
        """
        user_entity = UserEntity.by_oid(user_oid)
        return UserDTO.from_user_entity(user_entity)

    @staticmethod
    async def get_user_with_access_by_oid(
        user_oid: str, runner: "Runner", nc: NATS, t: LocaleHandler
    ) -> UserWithAccessDTO:
        """
        Retrieve a user with their access rules.
        """
        user_entity = UserEntity.by_oid(user_oid)
        return await UserWithAccessDTO.from_user_entity(user_entity, runner, nc, t)

    @staticmethod
    async def get_paginated_users(page: int = 1, page_size: int = 20) -> tuple[int, list[UserDTO]]:
        """
        Retrieve a paginated list of users from the database.
        """
        skip = (page - 1) * page_size
        total = UserEntity.count_users()
        user_entities = UserEntity.get_paginated_users(skip=skip, limit=page_size)

        user_dtos = [UserDTO.from_user_entity(user) for user in user_entities]

        return total, user_dtos
