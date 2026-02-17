"""
AI-Hub OpenAI-Compatible Open-WebUI Pipeline

This pipeline provides native integration between AI-Hub agents and Open-WebUI through
OpenAI's standard chat completions API. It uses the /openai endpoint instead of the
agent-specific SSE streaming endpoints, providing a more standardized approach.

Key Features:
- OpenAI-compatible chat completions interface
- Support for both streaming and non-streaming responses
- Standard OpenAI message format
- Agent discovery through model listing
- File upload support
- Authentication and error handling

Architecture:
- Uses /openai/chat/completions endpoint for agent communication
- Agents are accessed using "agent_class/agent_id" model naming
- Streaming responses use standard OpenAI SSE format
- Authentication via Bearer token with user headers
"""

import hashlib
import hmac
import json
import logging
import os
import urllib.parse
from typing import Any, Annotated

import httpx
from pydantic import BaseModel, Field
from bson import ObjectId

logger = logging.getLogger(__name__)


# ============================================================================
# Authentication Service
# ============================================================================


class AuthenticationService:
    """Handles all authentication-related operations"""

    def __init__(
        self,
        signing_secret: Annotated[str, "HMAC signing secret"],
        api_key: Annotated[str, "API key for AI-Hub"],
    ):
        self._signing_secret = signing_secret
        self._api_key = api_key

    def sign_user_headers(
        self,
        user_name: Annotated[str, "User's name"],
        user_email: Annotated[str, "User's email address"],
    ) -> Annotated[str, "HMAC-SHA256 signature as hex string"]:
        """Generate HMAC-SHA256 signature for user authentication"""
        secret = self._signing_secret.encode("utf-8")
        message = f"name:{user_name},email:{user_email}".encode()
        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    def prepare_headers(
        self,
        user_name: Annotated[str, "User's name"],
        user_email: Annotated[str, "User's email address"],
    ) -> Annotated[dict[str, str], "HTTP headers with authentication"]:
        """Prepare authenticated request headers"""
        clean_username = urllib.parse.quote(user_name, safe="") if user_name else ""
        signature = self.sign_user_headers(clean_username, user_email)

        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-OpenWebUI-User-Name": clean_username,
            "X-OpenWebUI-User-Email": user_email,
            "X-OpenWebUI-Signature": signature,
        }


# ============================================================================
# Main Pipe
# ============================================================================


class Pipe:
    """
    AI-Hub OpenAI-Compatible Pipeline - Main Pipe

    This pipeline provides OpenAI-compatible access to AI-Hub agents through
    the standardized chat completions API instead of agent-specific SSE endpoints.
    """

    class Valves(BaseModel):
        """Configuration valves for the pipeline"""

        AIHUB_BASE_URL: str = Field(
            default=os.getenv("AIHUB_BASE_URL", "http://localhost:8000"),
            description="Base URL for the AI-Hub API endpoints",
        )
        AIHUB_SUPERUSER_API_KEY: str = Field(
            default=os.getenv("AIHUB_SUPERUSER_API_KEY", ""),
            description="API key for authenticating with AI-Hub",
        )
        OPEN_WEBUI_SIGNING_SECRET: str = Field(
            default=os.getenv("OPEN_WEBUI_SIGNING_SECRET", ""),
            description="Secret key for signing user headers",
        )
        AIHUB_OPENAI_PIPELINE_PREFIX: str = Field(
            default=os.getenv("AIHUB_OPENAI_PIPELINE_PREFIX", "openai/"),
            description="Prefix added to model names in the UI",
        )
        AIHUB_REQUEST_TIMEOUT: int = Field(
            default=int(os.getenv("AIHUB_REQUEST_TIMEOUT", "60")),
            description="Request timeout in seconds",
        )

    def __init__(self):
        self.valves = self.Valves()
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize all required services"""
        # Authentication
        self._auth_service = AuthenticationService(
            self.valves.OPEN_WEBUI_SIGNING_SECRET, self.valves.AIHUB_SUPERUSER_API_KEY
        )

    async def pipes(
        self,
    ) -> Annotated[list[dict[str, str]], "List of available model pipelines"]:
        """Discover available LLM models via OpenAI models endpoint"""
        if not self._validate_configuration():
            return [{"id": "error", "name": "Configuration incomplete"}]
        try:
            headers = {
                "Authorization": f"Bearer {self.valves.AIHUB_SUPERUSER_API_KEY}",
                "Accept": "application/json",
            }

            async with httpx.AsyncClient(
                timeout=self.valves.AIHUB_REQUEST_TIMEOUT, follow_redirects=True
            ) as client:
                response = await client.get(
                    f"{self.valves.AIHUB_BASE_URL}/api/v1/openai/models",
                    headers=headers,
                )
                response.raise_for_status()
                models_data = response.json()
                print("Models data:", models_data)
                return [
                    {
                        "id": model["id"],
                        "name": f"{self.valves.AIHUB_OPENAI_PIPELINE_PREFIX}{model.get('name', model['id'])}",
                    }
                    for model in models_data.get("data", [])
                ]
        except Exception as e:
            logger.exception(f"Error fetching models: {e}")
            return [{"id": "error", "name": f"Error: {str(e)}"}]

    def _validate_configuration(self) -> Annotated[bool, "Configuration validity"]:
        """Validate required configuration"""
        return bool(
            self.valves.AIHUB_SUPERUSER_API_KEY
            and self.valves.OPEN_WEBUI_SIGNING_SECRET
        )

    def _extract_model_id(
        self, model_id_with_pipe_prefix: Annotated[str, "Model ID from request"]
    ) -> Annotated[str, "Clean model ID"]:
        """Extract clean model ID (remove pipeline prefix if present)"""
        parts = model_id_with_pipe_prefix.split(".")
        if len(parts) < 2:
            raise ValueError(f"Invalid model ID format: {model_id_with_pipe_prefix}")

        model_id = parts[1]

        if model_id.startswith(self.valves.AIHUB_OPENAI_PIPELINE_PREFIX):
            return model_id[len(self.valves.AIHUB_OPENAI_PIPELINE_PREFIX) :]
        return model_id

    def _str_to_object_id(self, context_id: str | None) -> str:
        if not context_id:
            return str(ObjectId())
        hashed = hashlib.md5(context_id.encode()).digest()[:12]
        return str(ObjectId(hashed))

    async def pipe_stream(
        self,
        body: Annotated[dict[str, Any], "Request body"],
        __user__: Annotated[dict[str, str], "User information"],
        __metadata__: Annotated[dict[str, str], "Request metadata"],
        __request__: Annotated[Any, "Request"],
    ):
        """
        Handle streaming requests, yielding SSE formatted strings.
        This is an async generator function that yields lines of streaming output.
        """
        # Prepare headers and payload
        headers = self._auth_service.prepare_headers(
            __user__["name"], __user__["email"]
        )
        model_id = self._extract_model_id(body["model"])
        thread_id = self._str_to_object_id(__metadata__.get("chat_id"))
        display_id = self._str_to_object_id(__metadata__.get("message_id"))

        payload = {
            **body,
            "model": model_id,
            "metadata": {
                "thread_id": thread_id,
                "display_id": display_id,
            },
        }

        client = httpx.AsyncClient(timeout=None, follow_redirects=True)

        try:
            # Start the streaming request
            async with client.stream(
                "POST",
                url=f"{self.valves.AIHUB_BASE_URL}/api/v1/openai/chat/completions",
                json=payload,
                headers=headers,
            ) as stream_response:
                # Process the stream line by line
                async for line in stream_response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue

                    # Format and yield as SSE string
                    if line.startswith("data:"):
                        yield f"{line}\n\n"
                    elif line == "[DONE]":
                        yield f"data: {line}\n\n"
                        break
                    else:
                        yield f"data: {line}\n\n"

                    # Check for finish_reason to detect stream end
                    if line.startswith("data: "):
                        try:
                            data_content = line[6:]
                            if data_content != "[DONE]":
                                data = json.loads(data_content)
                                if data.get("choices", [{}])[0].get("finish_reason"):
                                    # Stream near completion, but don't break yet
                                    pass
                        except Exception:
                            # Ignore JSON parsing errors
                            pass

                # Close the response when streaming is done
                await stream_response.aclose()

        except httpx.HTTPStatusError as e:
            try:
                error_body = await e.response.aread()
                error_detail = error_body.decode()
            except Exception:
                error_detail = "(Could not decode error body)"

            logger.exception(
                f"HTTP error during streaming: {e.response.status_code} - {error_detail}"
            )
            yield f"data: {json.dumps({'error': f'API Error: Status {e.response.status_code}'})}\n\n"

        except Exception as e:
            logger.exception(f"Error during streaming: {e}")
            yield f"data: {json.dumps({'error': f'Request error: {str(e)}'})}\n\n"

        finally:
            # Always close the client when we're done
            await client.aclose()

    async def pipe_non_stream(
        self,
        body: Annotated[dict[str, Any], "Request body"],
        __user__: Annotated[dict[str, str], "User information"],
        __metadata__: Annotated[dict[str, str], "Request metadata"],
        __request__: Annotated[Any, "Request"],
    ):
        """
        Handle non-streaming requests, returning a dict with the completion response.
        This is a regular async function that returns a dictionary.
        """
        headers = self._auth_service.prepare_headers(
            __user__["name"], __user__["email"]
        )
        model_id = self._extract_model_id(body["model"])
        thread_id = self._str_to_object_id(__metadata__.get("chat_id"))
        display_id = self._str_to_object_id(__metadata__.get("message_id"))

        payload = {
            **body,
            "model": model_id,
            "metadata": {
                "thread_id": thread_id,
                "display_id": display_id,
            },
        }

        try:
            # Use a separate client for non-streaming requests
            async with httpx.AsyncClient(
                timeout=self.valves.AIHUB_REQUEST_TIMEOUT, follow_redirects=True
            ) as client:
                response = await client.post(
                    url=f"{self.valves.AIHUB_BASE_URL}/api/v1/openai/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                completion_response = response.json()

            # Return the complete response for non-streaming
            return completion_response

        except httpx.HTTPStatusError as e:
            try:
                error_body = await e.response.aread()
                error_detail = error_body.decode()
            except Exception:
                error_detail = "(Could not decode error body)"

            logger.exception(f"HTTP error: {e.response.status_code} - {error_detail}")
            return {
                "error": f"API Error: Status {e.response.status_code} - {error_detail}"
            }

        except Exception as e:
            logger.exception(f"Error during non-streaming request: {e}")
            return {"error": f"Request error: {str(e)}"}

    async def pipe(
        self,
        body: Annotated[dict[str, Any], "Request body"],
        __user__: Annotated[dict[str, str], "User information"],
        __metadata__: Annotated[dict[str, str], "Request metadata"],
        __request__: Annotated[Any, "Request"],
    ) -> Annotated[str, "Response (always empty for streaming)"]:
        """Main pipeline entry point"""

        is_streaming = body.get("stream", False)
        logger.debug(
            f"Request type: {'streaming' if is_streaming else 'non-streaming'}"
        )

        if is_streaming:
            # For streaming, we return the async generator object directly
            return self.pipe_stream(body, __user__, __metadata__, __request__)
        else:
            # For non-streaming, we await the result and return it
            return await self.pipe_non_stream(body, __user__, __metadata__, __request__)
