from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Security

from aihub_api.routes.model.dto.ModelDTO import ModelDTO, ModelTypeGroupDTO
from aihub_api.routes.model.ModelService import ModelService


class ModelController(Controller):
    """
    A controller managing endpoints related to available models.

    ### Why ModelController?
    The ModelController exposes routes for:
    - Listing all available models.
    - Retrieving information about a specific model.
    """

    name = LocaleString(en="AI Models", de="KI-Modelle", fr="Modèles IA", it="Modelli IA")
    description = LocaleString(
        en="View available AI models",
        de="Verfügbare KI-Modelle anzeigen",
        fr="Consultez les modèles IA disponibles",
        it="Visualizza i modelli IA disponibili",
    )
    icon = "meteor-icons:key"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/models", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_models(self, route: str = "") -> "ModelController":
        @self.router.get(route, tags=self.tags)
        async def get_models(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> list[ModelTypeGroupDTO]:
            """Retrieve a list of all available models grouped by type."""
            return await ModelService.get_grouped_model_list(user)

        return self

    def get_model(self, route: str = "/{model_name:path}") -> "ModelController":
        @self.router.get(route, tags=self.tags)
        async def get_model(
            model_name: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> ModelDTO:
            """Retrieve a specific model by name."""
            return await ModelService.get_model_by_name(user, model_name)

        return self
