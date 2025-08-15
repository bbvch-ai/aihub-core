from typing import Annotated

from fastapi import Depends, HTTPException, Security

from aihub_api.routes.model.ModelService import ModelService
from aihub_api.routes.model.dto.ModelDTO import ModelDTO
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
    """

    name = LocaleString(en="Models")
    description = LocaleString(en="Shows all available models.")
    icon = "meteor-icons:key"

    not_authorized_to_view_exception = HTTPException(status_code=403, detail="Not authorized to view this thread")

    def __init__(
        self, *, auth: AuthHandler, route: str = "/models", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def status(self, route: str = "/") -> "ModelController":
        @self.router.get(route, tags=self.tags)
        async def status(
            user: Annotated[UserIdentity, Depends(self.auth)],
        ) -> dict:
            """
            Get model service status.
            """
            return {"status": "ok", "service": "litellm"}

        return self

    def model_list(self, route: str = "/model_list") -> "ModelController":
        @self.router.get(route, tags=self.tags)
        async def model_list(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> list[ModelDTO]:
            """
            Retrieve a list of all available models.
            """
            data = await ModelService.get_model_list(user)
            return data

        return self
