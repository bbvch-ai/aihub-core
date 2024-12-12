import logging
from typing import Callable, Any

from fastapi import APIRouter, Body, Path, Depends, Request
from starlette.responses import StreamingResponse

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.routes.chat.dto.ChatCompletionsRequest import ChatCompletionsRequest
from api_core.routes.chat.dto.json.ChatCompletionsSuccessResponse import ChatCompletionsSuccessResponse

from .service import (
    start_stream_chat_interaction,
    start_json_chat_interaction,
    build_json_response,
    create_sse_generator,
    StreamingResources,
    JsonResources
)

logger = logging.getLogger(__name__)


def chat_controller_factory(user_auth_strategy: Callable[..., Any]) -> APIRouter:
    chat_router = APIRouter()

    @chat_router.post(
        "/completions/{agent_class}/{agent_id}/stream",
        summary="Stream Chat",
        description="Initiates a streaming interaction with a specific agent. This endpoint requires authentication, checks user roles and spending limits, and supports file uploads.",
        tags=["Agent"],
        responses={
            200: {
                "description": "Successful streaming response",
                "content": {
                    "text/event-stream": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "object": {
                                    "type": "string",
                                    "enum": ["chat.completion.chunk"],
                                },
                                "created": {"type": "integer"},
                                "model": {"type": "string"},
                                "choices": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "index": {"type": "integer"},
                                            "finish_reason": {
                                                "type": "string",
                                                "nullable": True,
                                            },
                                            "delta": {
                                                "type": "object",
                                                "properties": {
                                                    "role": {
                                                        "type": "string",
                                                        "nullable": True,
                                                    },
                                                    "content": {"type": "string"},
                                                },
                                            },
                                        },
                                    },
                                },
                                "usage": {"type": "object", "nullable": True},
                            },
                        },
                        "example": """
data: {"id":"5511afde-7f5e-4892-bc7d-ed1bdf73830a","object":"chat.completion.chunk","created":1734012911,"model":"gpt-4","choices":[{"index":0,"finish_reason":null,"delta":{"role":"assistant","content":"First chunk.\n"}}],"usage":null}
data: {"id":"298742bb-7d1c-41a5-bbda-faaaa8100c9e","object":"chat.completion.chunk","created":1734012911,"model":"gpt-4","choices":[{"index":0,"finish_reason":null,"delta":{"role":"assistant","content":"Second chunk"}}],"usage":null}
data: {"id":"c577309c-7954-4dba-9de5-311a679e335b","object":"chat.completion.chunk","created":1734012912,"model":"","choices":[{"index":0,"finish_reason":"stop","delta":{"role":"assistant","content":""}}],"usage":null}
        """,
                        "description": "A stream of server-sent events. Each event is prefixed with 'data: ' and separated by two newline characters. The content of each event is a JSON object representing a chat completion chunk.",
                    }
                },
            },
            401: {"description": "Unauthorized access"},
            403: {"description": "Forbidden - user lacks appropriate access or has exceeded spending limits"},
            404: {"description": "Organization or agent not found"},
        },
        response_class=StreamingResponse,
    )
    async def stream_chat(
        request: Request,
        chat_completions_request: ChatCompletionsRequest = Body(...),
        agent_class: str = Path(...),
        agent_id: str = Path(...),
        user: AuthenticatedUser = Depends(user_auth_strategy),
    ) -> StreamingResponse:
        resources: StreamingResources = await start_stream_chat_interaction(
            request.app.state,
            user,
            agent_class,
            agent_id,
            chat_completions_request,
        )
        return StreamingResponse(
            create_sse_generator(resources.stop_event, resources.chunk_queue),
            media_type="text/event-stream"
        )

    @chat_router.post(
        "/completions/{agent_class}/{agent_id}/json",
        description="Initiates an interaction with a specific agent and returns a JSON response. This endpoint requires authentication, checks user roles and spending limits, and supports file uploads.",
        tags=["Agent"],
        responses={
            200: {"description": "Successful response with chat completion data"},
            401: {"description": "Unauthorized access"},
            403: {"description": "Forbidden - user lacks appropriate access or has exceeded spending limits"},
            404: {"description": "Organization or agent not found"},
        },
    )
    async def json_chat(
        request: Request,
        chat_completions_request: ChatCompletionsRequest = Body(...),
        agent_class: str = Path(...),
        agent_id: str = Path(...),
        user: AuthenticatedUser = Depends(user_auth_strategy),
    ) -> ChatCompletionsSuccessResponse:
        resources: JsonResources = await start_json_chat_interaction(
            request.app.state,
            user,
            agent_class,
            agent_id,
            chat_completions_request,
        )

        # Wait for the stop_event which signals that all events have been processed
        await resources.stop_event.wait()
        await resources.subscriber.stop()

        # Now resources.costs and resources.model_name have been updated by the aggregator
        return build_json_response(resources.chunk_events, resources.costs, resources.model_name)

    return chat_router
