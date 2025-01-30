import logging
from typing import Callable, Any, Annotated

from fastapi import Body, Path, Depends, Request
from starlette.responses import StreamingResponse
from nats.aio.client import Client as NATS

from aihub_api.auth.AuthenticatedUser import AuthenticatedUser
from aihub_api.routes.chat.dto.ChatCompletionsRequest import ChatCompletionsRequest
from aihub_api.routes.chat.dto.json.ChatCompletionsSuccessResponse import ChatCompletionsSuccessResponse
from aihub_api.sockets.receiver.WebSocketReceiver import WebSocketReceiver

from .ChatService import ChatService, StreamingResources, JsonResources
from ..Controller import Controller
from ...nats.dependencies.use_nats import use_nats
from ...sockets.receiver.dependencies.use_ws_receiver import use_ws_receiver

logger = logging.getLogger(__name__)


class ChatController(Controller):
    """
    A controller exposing endpoints for initiating chat completions, both streaming and JSON-based.

    ### Why ChatController?
    In complex AI-driven workflows, users often need to:
    - Send a sequence of messages to an agent.
    - Receive responses in either streaming mode (Server-Sent Events) or JSON mode.

    The `ChatController` defines these HTTP endpoints, ensuring authentication, parameter handling,
    and integration with the underlying `ChatService`.

    ### Endpoints
    - `POST /completions/{agent_class}/{agent_id}/stream`:
      Initiates a streaming chat interaction. The server returns SSE (Server-Sent Events) that stream chunks
      of the agent’s response as they are ready.

    - `POST /completions/{agent_class}/{agent_id}/json`:
      Initiates a chat interaction and returns a JSON response after the entire conversation is processed.

    ### Authentication & Authorization
    Both endpoints require an authenticated user. The user’s permissions and spending limits are checked
    to ensure they can interact with the specified agent.

    ### File Uploads and Complex Requests
    These endpoints are designed to handle not just simple text messages, but potentially file uploads
    and other forms of user input. By integrating with `ChatService`, the logic remains clean and testable.
    """

    def __init__(self, route: str = "/chat", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def completions_stream(self, route: str = "/completions/{agent_class}/{agent_id}/stream") -> "ChatController":
        @self.router.post(
            route,
            summary="Stream Chat",
            description=(
                "Initiates a streaming interaction with a specific agent. "
                "Requires authentication and role checks. Returns textual responses as SSE."
            ),
            tags=["Agent"],
            responses={
                200: {"description": "Successful streaming response (SSE)"},
                401: {"description": "Unauthorized access"},
                403: {"description": "Forbidden - user lacks appropriate access or exceeded limits"},
                404: {"description": "Agent not found"},
            },
            response_class=StreamingResponse,
        )
        async def stream_chat(
            chat_completions_request: Annotated[ChatCompletionsRequest, Body],
            agent_class: Annotated[str, Path(title="Agent class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            ws_receiver: Annotated[WebSocketReceiver, Depends(use_ws_receiver)],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> StreamingResponse:
            """
            Start a streaming chat interaction. Streams chunks of the agent's response as SSE.
            """
            resources: StreamingResources = await ChatService.start_stream_chat_interaction(
                user,
                agent_class,
                agent_id,
                chat_completions_request,
                nc=nc,
                ws_receiver=ws_receiver,
            )
            return StreamingResponse(
                ChatService.create_sse_generator(resources.stop_event, resources.chunk_queue),
                media_type="text/event-stream",
            )

        return self

    def completions_json(self, route: str = "/completions/{agent_class}/{agent_id}/json") -> "ChatController":
        @self.router.post(
            route,
            description=(
                "Initiates a chat interaction with a specific agent and returns a full JSON response "
                "once all tokens are processed. Requires authentication and checks user limits."
            ),
            tags=["Agent"],
            responses={
                200: {"description": "Successful JSON response with chat completions"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - insufficient permissions or exceeded limits"},
                404: {"description": "Agent not found"},
            },
        )
        async def json_chat(
            chat_completions_request: Annotated[ChatCompletionsRequest, Body],
            agent_class: Annotated[str, Path(title="Agent class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            ws_receiver: Annotated[WebSocketReceiver, Depends(use_ws_receiver)],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ChatCompletionsSuccessResponse:
            """
            Start a chat interaction and return a JSON response after all tokens have been processed.
            """
            resources: JsonResources = await ChatService.start_json_chat_interaction(
                user,
                agent_class,
                agent_id,
                chat_completions_request,
                nc=nc,
                ws_receiver=ws_receiver,
            )

            # Wait until all events are processed
            await resources.stop_event.wait()
            await resources.subscriber.stop()

            # Construct final JSON response
            return ChatService.build_json_response(resources.chunk_events, resources.costs, resources.model_name)

        return self
