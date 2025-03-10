import logging
from typing import Annotated, Any, Callable, List

from botbuilder.integration.aiohttp import CloudAdapter
from fastapi import Body, Query, Request, Response
from llama_index.llms.openai import OpenAI

from aihub_bot.bots.openai.OpenaiChatBot import OpenaiChatBot
from aihub_bot.bots.openai.StreamOpenaiChatBot import StreamOpenaiChatBot
from aihub_bot.routes.activity_model import ActivityModel
from aihub_bot.routes.openai.OpenaiChatService import OpenaiChatService
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.routes.Controller import Controller

logger = logging.getLogger(__name__)


class OpenaiChatController(Controller):
    def __init__(
        self,
        route: str = "/openai/chat",
        is_admin_only=False,
        auth: Callable[..., Any] = None,
        chat_models: List[ChatLLMConfig] = None,
    ):
        super().__init__(route, auth, is_admin_only=is_admin_only)
        self.chat_models = chat_models or []

        for chat_model in self.chat_models:
            model, _ = chat_model.to_llama_index()
            if not isinstance(model, OpenAI):
                raise ValueError(f"Chat model {chat_model.name} is not an OpenAI compatible model.")

    def json_chat_completion(
        self,
        route: str = "/completions/json",
    ) -> "OpenaiChatController":
        @self.router.post(route)
        async def json_chat_completion(
            request: Request,
            _: Annotated[ActivityModel, Body],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            client = OpenaiChatService.get_client(self.chat_models, model_name)
            path = OpenaiChatService.get_path(request)
            chat_bot = OpenaiChatBot(model_name, client, path)
            adapter: CloudAdapter = OpenaiChatService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self

    def stream_chat_completion(
        self,
        route: str = "/completions/stream",
    ) -> "OpenaiChatController":
        @self.router.post(route)
        async def stream_chat_completion(
            request: Request,
            _: Annotated[ActivityModel, Body],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            client = OpenaiChatService.get_client(self.chat_models, model_name)
            path = OpenaiChatService.get_path(request)
            chat_bot = StreamOpenaiChatBot(model_name, client, path)
            adapter: CloudAdapter = OpenaiChatService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self
