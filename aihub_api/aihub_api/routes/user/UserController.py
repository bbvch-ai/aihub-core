from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from fastapi import Body, Depends, Path, Security
from nats.aio.client import Client as NATS

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.PaginatedUsersResponse import PaginatedUsersResponse
from aihub_api.routes.user.dto.UserWithAccessDTO import UserWithAccessDTO
from aihub_api.routes.user.UserService import UserService


class UserController(Controller):
    """
    A controller that manages user-related endpoints, particularly retrieving the currently logged-in user.

    ### Why UserController?
    In many applications, authenticated users may want to retrieve their own profile or check who they are
    logged in as. The `UserController` provides a simple endpoint that returns a `MinimalUserDTO`
    for the authenticated user.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.user.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.user.description")
    icon = "mage:user"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/users", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_users(self, route: str = "/") -> Self:
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

    def get_my_user(self, route: str = "/me") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_my_user(
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> UserWithAccessDTO:
            """
            Returns a `MinimalUserDTO` representing the currently logged-in user.
            """
            return await UserService.get_logged_in_user(user, runner=self._runner, nc=nc, t=t)

        return self

    def get_user(self, route: str = "/{user_id}") -> Self:
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

    def get_my_dashboard(self, route: str = "/me/dashboard") -> Self:
        """
        Registers an endpoint to retrieve the currently logged-in user's dashboard settings.
        """

        @self.router.get(route, tags=self.tags)
        async def get_my_dashboard(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> DashboardDTO | None:
            """
            Returns a `DashboardDTO` representing the user's dashboard settings, or null if none exist.
            """
            return UserService.get_user_dashboard(user)

        return self

    def update_my_dashboard(self, route: str = "/me/dashboard") -> Self:
        """
        Registers an endpoint to update the currently logged-in user's dashboard settings.
        """

        @self.router.put(route, tags=self.tags, status_code=204)
        async def update_my_dashboard(
            dashboard_dto: Annotated[DashboardDTO, Body],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> None:
            """
            Updates the user's dashboard settings.
            Accepts a `DashboardDTO` in the request body.
            """
            await UserService.update_user_dashboard(user, dashboard_dto)
            return None

        return self
