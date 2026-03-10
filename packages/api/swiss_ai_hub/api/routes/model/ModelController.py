from typing import Annotated, Self

from fastapi import Security
from swiss_ai_hub.core.auth.dependencies.AuthHandler import AuthHandler
from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.routes.Controller import Controller

from swiss_ai_hub.api.i18n.ApiLocaleString import ApiLocaleString
from swiss_ai_hub.api.routes.model.dto.ModelDTO import ModelDTO, ModelTypeGroupDTO
from swiss_ai_hub.api.routes.model.ModelService import ModelService


class ModelController(Controller):
    """
    A controller managing endpoints related to available models.

    ### Why ModelController?
    The ModelController exposes routes for:
    - Listing all available models.
    - Retrieving information about a specific model.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.model.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.model.description")
    icon = "mage:key"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/models", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_litellm_models(self, route: str = "") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_litellm_models(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> list[ModelTypeGroupDTO]:
            """Retrieve a list of all available models grouped by type."""
            return await ModelService.get_grouped_model_list(user)

        return self

    def get_litellm_model(self, route: str = "/{model_name:path}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_litellm_model(
            model_name: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> ModelDTO:
            """Retrieve a specific model by name."""
            return await ModelService.get_model_by_name(user, model_name)

        return self

    def get_litellm_models_by_mode(self, route: str = "/mode/{mode}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_litellm_models_by_mode(
            mode: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> list[ModelDTO]:
            """Retrieve all models filtered by their mode (chat, embedding, rerank, etc.)."""
            return await ModelService.get_models_by_mode(user, mode)

        return self
