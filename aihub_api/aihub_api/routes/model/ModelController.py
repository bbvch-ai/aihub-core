from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Security
from nats.aio.client import Client as NATS

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.model.dto.ModelDTO import ModelDTO
from aihub_api.routes.model.ModelService import ModelService


class ModelController(Controller):
    """
    A controller managing endpoints related to LiteLLM, in order to manage and interact with LiteLLM functionalities.

    ### Why AgentController?
    The AgentController exposes routes for:
    - Listing all available LiteLLM models.
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
            Get LiteLLM service status.
            """
            return {"status": "ok", "service": "litellm"}

        return self

    def model_list(self, route: str = "/model_list") -> "ModelController":
        @self.router.get(route, tags=self.tags)
        async def model_list(
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[ModelDTO]:
            """
            Retrieve a list of all models in LiteLLM.
            """
            data = await ModelService.get_model_list(user)
            return data

        return self
