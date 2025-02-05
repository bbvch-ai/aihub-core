import asyncio
import logging
from typing import Any, Callable, List, Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, Body
from llama_index.llms.openai import OpenAI
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion
from starlette.responses import StreamingResponse

from aihub_lib.generative_ai.llms.models.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.generative_ai.llms.models.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig
from .dto.ChatCompletionRequest import ChatCompletionRequest
from .dto.Embeddings import Embeddings
from .dto.EmbeddingsRequest import EmbeddingsRequest
from .dto.EmbeddingsResponse import EmbeddingsResponse
from .dto.ModelDetails import ModelDetails
from .dto.ModelResponse import ModelResponse
from ..Controller import Controller
from ...auth.AuthenticatedUser import AuthenticatedUser

logger = logging.getLogger(__name__)


class OpenaiController(Controller):

    def __init__(
            self,
            route: str = "/openai",
            auth: Callable[..., Any] = None,
            embedding_models: List[EmbeddingLLMConfig] = None,
            chat_models: List[ChatLLMConfig] = None,

         ):
        super().__init__(route, auth)
        self.embedding_models = embedding_models or []
        self.chat_models = chat_models or []

        for chat_model in self.chat_models:
            model, _ = chat_model.to_llama_index()
            if not isinstance(model, OpenAI):
                raise ValueError(f"Chat model {chat_model.name} is not an OpenAI compatible model.")

    def get_models(self, route: str = "/models") -> "OpenaiController":
        @self.router.get(route)
        async def get_models(
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ModelResponse:
            models = [ModelDetails(id=model.name) for model in self.chat_models]
            return ModelResponse(data=models)

        return self

    def get_model(self, route: str = "/models/{model_name}") -> "OpenaiController":
        @self.router.get(route)
        async def get_model(
            model_name: str,
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ModelDetails:
            models = [ModelDetails(id=model.name) for model in self.chat_models if model.name == model_name]
            if len(models) == 0:
                raise HTTPException(status_code=404, detail="Model not found.")
            return ModelDetails(id=models[0].name)

        return self

    def get_embeddings(self, route: str = "/embeddings") -> "OpenaiController":
        @self.router.post(route)
        async def get_embeddings(
            req: EmbeddingsRequest,
            user: AuthenticatedUser = Depends(self.auth),
        ) -> EmbeddingsResponse:
            try:
                embedding_model_config = next((model for model in self.embedding_models if model.name == req.model), None)
            except StopIteration:
                raise HTTPException(status_code=404, detail="Model not found.")

            embedding_model, cost_tracker = embedding_model_config.to_llama_index()
            inputs = req.input if isinstance(req.input, list) else [req.input]
            embeddings = embedding_model.get_text_embedding_batch(inputs)
            return EmbeddingsResponse(
                model=req.model,
                data=[Embeddings(index=i, embedding=embedding) for i, embedding in enumerate(embeddings)],
            )

        return self

    def chat_completion(self, route: str = "/chat/completions") -> "OpenaiController":
        @self.router.post(route)
        async def chat_completion(
            completion_request: Annotated[ChatCompletionRequest, Body],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ChatCompletion | StreamingResponse:
            try:
                chat_model_config = next((model for model in self.chat_models if model.name == completion_request.model), None)
            except StopIteration:
                raise HTTPException(status_code=404, detail="Model not found.")

            chat_model, _ = chat_model_config.to_llama_index()
            client: AsyncOpenAI | AsyncAzureOpenAI = chat_model._get_aclient()
            function_args = completion_request.model_dump()

            if completion_request.stream:
                async def stream_chat_completion(**kwargs) -> AsyncGenerator[str, None]:
                    """Handles streaming responses from OpenAI's API."""
                    response = await client.chat.completions.create(**kwargs)

                    async for chunk in response:
                        yield f"data: {chunk.model_dump_json()}\n\n"
                        await asyncio.sleep(0)
                return StreamingResponse(stream_chat_completion(**function_args), media_type="text/event-stream")
            else:
                return await client.chat.completions.create(**function_args)

        return self

    def generate_image(self, route: str = "/images/generations") -> "OpenaiController":
        @self.router.post(route)
        async def generate_image(

        ):
            pass