from typing import Annotated, Self

from fastapi import Query, Security
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure import HostingLocation, ModelCapability, ModelRequirements
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.model.dto.model_dto import ModelDTO, ModelTypeGroupDTO
from swiss_ai_hub.api.routes.model.model_service import ModelService


class ModelController(TenantScopedController):
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
            capability: Annotated[list[ModelCapability] | None, Query()] = None,
            hosting_location: Annotated[list[HostingLocation] | None, Query()] = None,
            include_special_purpose: Annotated[bool, Query()] = False,
        ) -> list[ModelDTO]:
            """Retrieve the models of one mode (chat, embedding, rerank, etc.) a model picker may offer.

            Repeat `capability` to require several capabilities, and `hosting_location` to allow several locations; a
            model whose flag or location is not set fails them. Models built for one job, such as the OCR model, are
            left out unless `include_special_purpose` is set.
            """
            requirements = ModelRequirements(
                capabilities=frozenset(capability or ()),
                hosting_locations=frozenset(hosting_location) if hosting_location else None,
            )
            return await ModelService.get_models_by_mode(user, mode, requirements, include_special_purpose)

        return self
