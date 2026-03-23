from typing import Annotated, Self

from fastapi import Depends, HTTPException, Path, Security
from mongoengine.errors import DoesNotExist
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.dependencies import use_nats
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.pagination.type.page_number import PageNumber
from swiss_ai_hub.api.pagination.type.page_size import PageSize
from swiss_ai_hub.api.routes.user.dto.paginated_users_response import PaginatedUsersResponse
from swiss_ai_hub.api.routes.user.dto.user_with_access_dto import UserWithAccessDTO
from swiss_ai_hub.api.routes.user.user_service import UserService


class UserController(Controller):
    """Admin controller for managing users within a tenant."""

    name = ApiLocaleString.from_i18n_path("api.controllers.user.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.user.description")
    icon = "mage:users"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/users", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_users(self, route: str = "/") -> Self:
        """Registers an endpoint to retrieve a paginated list of users."""

        @self.router.get(route, tags=self.tags)
        async def get_users(
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> PaginatedUsersResponse:
            """Returns a paginated list of users within the requesting admin's tenant."""
            total, user_dtos = await UserService.get_paginated_users(
                tenant_id=user.acting_within_tenant.id, page=page, page_size=page_size
            )
            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
            return PaginatedUsersResponse(
                users=user_dtos,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

        return self

    def get_user(self, route: str = "/{user_id}") -> Self:
        """Registers an endpoint to retrieve a specific user by their OID."""

        @self.router.get(route, tags=self.tags)
        async def get_user(
            user_id: Annotated[str, Path(description="The user's unique identifier (OID).")],
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
        ) -> UserWithAccessDTO:
            """Retrieve user info by their OID. Shows access within the admin's current tenant context."""
            try:
                return await UserService.get_user_with_access_by_oid(
                    user_id, user.acting_within_tenant, runner=self._runner, nc=nc, t=t
                )
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="User not found.")

        return self
