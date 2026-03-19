import logging
from typing import Annotated, Self

from fastapi import Body, Query, Request, Response
from llama_index.llms.openai import OpenAI
from microsoft_agents.activity import Activity
from microsoft_agents.hosting.aiohttp import CloudAdapter
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.bot.bots.chat.openai.openai_chat_bot import OpenaiChatBot
from swiss_ai_hub.bot.bots.chat.openai.stream_openai_chat_bot import StreamOpenaiChatBot
from swiss_ai_hub.bot.routes.routes_service import RoutesService

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

    @staticmethod
    async def _process_chat_request(
        request: Request,
        model_name: str,
        bot_class: type[OpenaiChatBot],
        typing_timeout_seconds: int,
    ) -> Response:
        logger.info(f"Starting chat completion for model {model_name}")

        path = RoutesService.get_path(request)
        chat_bot = bot_class(model_name=model_name, path=path, typing_timeout_seconds=typing_timeout_seconds)
        adapter: CloudAdapter = RoutesService.get_adapter(path)

        result = await adapter.process(request, chat_bot)
        logger.info("Chat completion successful")
        return result

    def json_chat_completion(
        self,
        route: str = "/completions/json",
        typing_timeout_seconds: int = 60,
    ) -> Self:
        @self.router.post(route, tags=self.tags)
        async def json_chat_completion(
            request: Request,
            _: Annotated[Activity, Body],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            return await self._process_chat_request(
                request=request,
                model_name=model_name,
                bot_class=OpenaiChatBot,
                typing_timeout_seconds=typing_timeout_seconds,
            )

        return self

    def stream_chat_completion(
        self,
        route: str = "/completions/stream",
        typing_timeout_seconds: int = 60,
    ) -> Self:
        @self.router.post(route, tags=self.tags)
        async def stream_chat_completion(
            request: Request,
            _: Annotated[Activity, Body],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            return await self._process_chat_request(
                request=request,
                model_name=model_name,
                bot_class=StreamOpenaiChatBot,
                typing_timeout_seconds=typing_timeout_seconds,
            )

        return self
