from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Path, Security
from nats.aio.client import Client as NATS

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.user.dto.PaginatedUsersResponse import PaginatedUsersResponse
from aihub_api.routes.user.dto.UserWithAccessDTO import UserWithAccessDTO
from aihub_api.routes.user.UserService import UserService


class UserController(Controller):
    """
    Controller for user administration (admin-only).

    Provides endpoints for administrators to view and manage all users in the system.
    For personal account management, see MyAccountController.
    """

    name = LocaleString(en="Users", de="Benutzer", fr="Utilisateurs", it="Utenti")
    description = LocaleString(
        en="Manage users in the system",
        de="Benutzer im System verwalten",
        fr="Gérer les utilisateurs du système",
        it="Gestisci gli utenti nel sistema",
    )
    icon = "mdi:account-group"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        route: str = "/users",
        additionally_required_permission: str | None = "aihub.admin.service.user",
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_users(self, route: str = "/") -> "UserController":
        """
        Registers an endpoint to retrieve a paginated list of users.
        """

        @self.router.get(route, tags=self.tags)
        async def get_users(
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> PaginatedUsersResponse:
            """
            Returns a paginated list of all users.
            """
            total, user_dtos = await UserService.get_paginated_users(page=page, page_size=page_size)
            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
            return PaginatedUsersResponse(
                users=user_dtos,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

        return self

    def get_user(self, route: str = "/{user_id}") -> "UserController":
        """
        Registers an endpoint to retrieve a specific user by their OID.
        """

        @self.router.get(route, tags=self.tags)
        async def get_user(
            user_id: Annotated[str, Path(description="The user's unique identifier (OID).")],
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
        ) -> UserWithAccessDTO:
            """
            Retrieve user info by their OID.
            """
            return await UserService.get_user_with_access_by_oid(user_id, runner=self._runner, nc=nc, t=t)

        return self
