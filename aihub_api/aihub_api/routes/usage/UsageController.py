from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Security

from aihub_api.routes.usage.dto.UserUsageDTO import UserUsageDTO
from aihub_api.routes.usage.UsageService import UsageService


class UsageController(Controller):
    """Controller for user usage and budget information."""

    name = LocaleString(en="Usage", de="Nutzung", fr="Utilisation", it="Utilizzo")
    description = LocaleString(
        en="View your usage and budget information",
        de="Nutzung und Budget-Informationen anzeigen",
        fr="Afficher vos informations d'utilisation et de budget",
        it="Visualizza le informazioni su utilizzo e budget",
    )
    icon = "solar:chart-bold"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/usage", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_my_usage(self, route: str = "/me") -> "UsageController":
        """Get the current user's usage and budget information."""

        @self.router.get(
            route,
            summary="Get My Usage",
            description="Retrieves the current user's usage statistics, spend, and budget limits.",
            tags=self.tags,
        )
        async def get_my_usage_endpoint(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> UserUsageDTO:
            return await UsageService.get_user_usage(user)

        return self
