from typing import Annotated

from fastapi import Security

from aihub_api.routes.model.ModelService import ModelService
from aihub_api.routes.model.dto.ModelDTO import ModelDTO, ModelTypeGroupDTO
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller


class ModelController(Controller):
    """
    A controller managing endpoints related to available models, in order to interact with them.

    ### Why ModelController?
    The ModelController exposes routes for:
    - Listing all available models.
    - Retrieving information about a specific model.
    """

    name = LocaleString(en="Models")
    description = LocaleString(en="Shows all available models.")
    icon = "meteor-icons:key"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/models", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def models(self, route: str = "") -> "ModelController":
        @self.router.get(route, tags=self.tags)
        async def models(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.models.?>"))],
        ) -> list[ModelTypeGroupDTO]:
            """
            Retrieve a list of all available models grouped by type.
            """
            data = await ModelService.get_grouped_model_list(user)
            return data

        return self

    def get_model(self, route: str = "/{model_name:path}") -> "ModelController":
        @self.router.get(route, tags=self.tags)
        async def get_model(
            model_name: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.models.?>"))],
        ) -> ModelDTO:
            """
            Retrieve a specific model by name.
            """
            data = await ModelService.get_model_by_name(user, model_name)
            return data

        return self
