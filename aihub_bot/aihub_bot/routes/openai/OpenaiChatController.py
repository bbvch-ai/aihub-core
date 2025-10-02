import asyncio
import logging
from typing import Annotated

import openai
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.litellm.LiteLLMService import LiteLLMService
from aihub_lib.routes.Controller import Controller
from botbuilder.integration.aiohttp import CloudAdapter
from fastapi import Body, Query, Request, Response, Security
from llama_index.llms.openai import OpenAI

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

    async def _process_chat_request(
        self,
        request: Request,
        user: UserIdentity,
        model_name: str,
        bot_class: type[OpenaiChatBot] | type[StreamOpenaiChatBot],
        typing_timeout_seconds: int,
    ) -> Response:
        logger.info(f"Starting chat completion for model {model_name}")

        try:
            client: openai.AsyncClient = await asyncio.wait_for(
                LiteLLMService.openai_aclient_for_user(user=user), timeout=30.0
            )
        except TimeoutError:
            logger.error("LiteLLM service call timed out after 30 seconds")
            return Response(status_code=504, content="Gateway timeout - LiteLLM service not responding")

        path = RoutesService.get_path(request)
        chat_bot = bot_class(
            model_name=model_name, client=client, path=path, typing_timeout_seconds=typing_timeout_seconds
        )
        adapter: CloudAdapter = RoutesService.get_adapter(path)

        adapter_task = asyncio.create_task(adapter.process(request, chat_bot))
        try:
            result = await asyncio.wait_for(adapter_task, timeout=120.0)
            logger.info("Chat completion successful")
            return result
        except TimeoutError:
            logger.error("Bot adapter processing timed out after 120 seconds")
            adapter_task.cancel()
            try:
                await adapter_task
            except asyncio.CancelledError:
                pass
            return Response(status_code=504, content="Gateway timeout - bot processing took too long")

    def json_chat_completion(
        self,
        route: str = "/completions/json",
        typing_timeout_seconds: int = 60,
    ) -> "OpenaiChatController":
        @self.router.post(route, tags=self.tags)
        async def json_chat_completion(
            request: Request,
            _: Annotated[ActivityModel, Body],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            return await self._process_chat_request(
                request=request,
                user=user,
                model_name=model_name,
                bot_class=OpenaiChatBot,
                typing_timeout_seconds=typing_timeout_seconds,
            )

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
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            return await self._process_chat_request(
                request=request,
                user=user,
                model_name=model_name,
                bot_class=StreamOpenaiChatBot,
                typing_timeout_seconds=typing_timeout_seconds,
            )

        return self
