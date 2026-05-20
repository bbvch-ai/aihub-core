# SPDX-License-Identifier: LicenseRef-Proprietary
from typing import Annotated, Self

from fastapi import Security
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.sysadmin_api.routes.whoami.dto.whoami_response import WhoamiResponse


class WhoamiController(Controller):
    """Same-origin endpoint sysadmin-web uses to learn the caller's sysadmin status.

    Authenticates any logged-in user and returns ``is_sys_admin`` from the JWT roles
    claim. Deliberately NOT gated with ``sys_admin_user()`` — non-sysadmins must receive
    ``{is_sys_admin: false}`` rather than a 403, so the middleware can branch cleanly.
    """

    def __init__(self, *, auth: AuthHandler, route: str = "/whoami"):
        super().__init__(auth=auth, route=route)

    def get_whoami(self, route: str = "/") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_whoami(
            user: Annotated[UserIdentity, Security(self.authenticated_user())],
        ) -> WhoamiResponse:
            """Returns the authenticated user's sysadmin status."""
            return WhoamiResponse(is_sys_admin=user.is_sys_admin)

        return self
