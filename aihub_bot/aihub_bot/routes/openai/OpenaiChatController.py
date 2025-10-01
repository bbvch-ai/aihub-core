import logging
from typing import Annotated

import openai

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.litellm.LiteLLMService import LiteLLMService
from aihub_lib.routes.Controller import Controller
from microsoft_agents.hosting.aiohttp import CloudAdapter
from fastapi import Body, Query, Request, Response, Security
from llama_index.llms.openai import OpenAI
from openai import AsyncAzureOpenAI, AsyncOpenAI

from aihub_bot.bots.chat.openai.OpenaiChatBot import OpenaiChatBot
from aihub_bot.bots.chat.openai.StreamOpenaiChatBot import StreamOpenaiChatBot
from aihub_bot.routes.activity_model import ActivityModel
from aihub_bot.routes.RoutesService import RoutesService

logger = logging.getLogger(__name__)


class OpenaiChatController(Controller):
    name = LocaleString(en="LLM Chat")
    description = LocaleString(en="Chat with LLMs")

    def __init__(
        self,
        *,
        auth: AuthHandler,
        route: str = "/openai/chat",
        additionally_required_permission: str | None = None,
        chat_models: list[LLMConfig] = None,
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)
        self.chat_models = chat_models or []

        for chat_model in self.chat_models:
            model, _ = chat_model.to_llama_index()
            if not isinstance(model, OpenAI):
                raise ValueError(f"Chat model {chat_model.name} is not an OpenAI compatible model.")

    def json_chat_completion(
        self,
        route: str = "/completions/json",
        typing_timeout_seconds: int = 60,
    ) -> "OpenaiChatController":
        @self.router.post(route, tags=self.tags)
        async def json_chat_completion(
            request: Request,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            client: openai.AsyncClient = await LiteLLMService.openai_aclient_for_user(user=user)

            path = RoutesService.get_path(request)

            chat_bot = OpenaiChatBot(
                model_name=model_name, client=client, path=path, typing_timeout_seconds=typing_timeout_seconds
            )

            adapter: CloudAdapter = RoutesService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self

    def stream_chat_completion(
        self,
        route: str = "/completions/stream",
        typing_timeout_seconds: int = 60,
    ) -> "OpenaiChatController":
        @self.router.post(route, tags=self.tags)
        async def stream_chat_completion(
            request: Request,
            _: Annotated[ActivityModel, Body],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            client = self.get_client(self.chat_models, model_name)
            path = RoutesService.get_path(request)

            chat_bot = StreamOpenaiChatBot(
                model_name=model_name, client=client, path=path, typing_timeout_seconds=typing_timeout_seconds
            )

            adapter: CloudAdapter = RoutesService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self

    @staticmethod
    def get_client(
        models: list[LLMConfig],
        model_name: str,
    ) -> AsyncOpenAI | AsyncAzureOpenAI:
        """
        ### What
        - Get the asynchronous `OpenAI` client for the specified model.

        ### Why
        - The client is needed to fetch completions from the OpenAI API.
        """
        matches = [model for model in models if model.name == model_name]
        if len(matches) == 0:
            raise ValueError(f"Model {model_name} not found.")
        model_config = matches[0]
        llm, _ = model_config.to_llama_index()
        return llm._get_aclient()
