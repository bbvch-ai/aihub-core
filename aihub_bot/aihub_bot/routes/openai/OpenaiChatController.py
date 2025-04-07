import logging
from typing import Annotated, Any, Callable, List

from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from botbuilder.integration.aiohttp import CloudAdapter
from fastapi import Body, Query, Request, Response
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
    icon = "material-symbols-light:chat-outline"

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
        @self.router.post(route, tags=self.tags)
        async def json_chat_completion(
            request: Request,
            _: Annotated[ActivityModel, Body],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            client = self.get_client(self.chat_models, model_name)
            path = RoutesService.get_path(request)
            chat_bot = OpenaiChatBot(model_name, client, path)
            adapter: CloudAdapter = RoutesService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self

    def stream_chat_completion(
        self,
        route: str = "/completions/stream",
    ) -> "OpenaiChatController":
        @self.router.post(route, tags=self.tags)
        async def stream_chat_completion(
            request: Request,
            _: Annotated[ActivityModel, Body],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> Response:
            client = self.get_client(self.chat_models, model_name)
            path = RoutesService.get_path(request)
            chat_bot = StreamOpenaiChatBot(model_name, client, path)
            adapter: CloudAdapter = RoutesService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self

    @staticmethod
    def get_client(
        models: List[ChatLLMConfig],
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
