"""
title: AI-Hub Agent Connector
description: Connects Open WebUI to AI-Hub agents with streaming support
author: AI-Hub Team
version: 1.0.0
required_open_webui_version: 0.6.0
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
from typing import Any, Union, Annotated, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field
from bson import ObjectId
from open_webui.models.files import Files

logger = logging.getLogger(__name__)


class Pipe:
    """
    AI-Hub Agent Connector Pipeline

    This pipeline connects Open WebUI to AI-Hub agents by:
    1. Discovering available conversational agents that are online
    2. Sending UserMessageEvents to agents
    3. Streaming back responses via Server-Sent Events (SSE)
    4. Authenticating requests with HMAC signatures
    5. Handling Human-in-the-Loop interactions
    6. Supporting file uploads from S3/MinIO storage
    """

    class Valves(BaseModel):
        AIHUB_BASE_URL: str = Field(
            default=os.getenv("AIHUB_BASE_URL", "http://localhost:8000/api/v1"),
            description="Base URL for the AI-Hub API endpoints",
        )
        AIHUB_SUPERUSER_API_KEY: str = Field(
            default=os.getenv("AIHUB_SUPERUSER_API_KEY", ""),
            description="API key for authenticating with AI-Hub",
        )
        OPEN_WEBUI_SIGNING_SECRET: str = Field(
            default=os.getenv("OPEN_WEBUI_SIGNING_SECRET", ""),
            description="Secret key for signing user headers with HMAC-SHA256",
        )
        AIHUB_PIPELINE_PREFIX: str = Field(
            default=os.getenv("AIHUB_PIPELINE_PREFIX", "aihub/"),
            description="Prefix added to agent names in the UI",
        )
        AIHUB_REQUEST_TIMEOUT: int = Field(
            default=int(os.getenv("AIHUB_REQUEST_TIMEOUT", "60")),
            description="Request timeout in seconds",
        )
        S3_STORAGE_ENDPOINT: str = Field(
            default=os.getenv("S3_ENDPOINT_URL", ""),
            description="S3/MinIO endpoint URL (e.g., http://localhost:9000)",
        )
        S3_STORAGE_ACCESS_KEY: str = Field(
            default=os.getenv("S3_ACCESS_KEY_ID", ""),
            description="S3/MinIO access key",
        )
        S3_STORAGE_SECRET_KEY: str = Field(
            default=os.getenv("S3_SECRET_ACCESS_KEY", ""),
            description="S3/MinIO secret key",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def _fetch_file_from_s3(
        self, s3_path: Annotated[str, "S3 path in format s3://bucket/key"]
    ) -> Annotated[Optional[bytes], "File content as bytes"]:
        """
        Fetch a file from S3/MinIO storage.
        """
        try:
            # Parse S3 path
            parsed = urlparse(s3_path)
            if parsed.scheme != "s3":
                logger.error(f"Invalid S3 path: {s3_path}")
                return None

            bucket = parsed.netloc
            key = parsed.path.lstrip("/")

            # Use boto3 if available, otherwise use direct HTTP requests
            try:
                import boto3
                from botocore.client import Config

                # Create S3 client
                s3_client = boto3.client(
                    "s3",
                    endpoint_url=self.valves.S3_STORAGE_ENDPOINT,
                    aws_access_key_id=self.valves.S3_STORAGE_ACCESS_KEY,
                    aws_secret_access_key=self.valves.S3_STORAGE_SECRET_KEY,
                    config=Config(signature_version="s3v4"),
                    region_name="us-east-1",  # Default region for MinIO
                )

                # Download file
                response = s3_client.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()

            except ImportError:
                # Fallback to direct HTTP requests for MinIO
                logger.debug("boto3 not available, using HTTP requests for S3")

                # Build URL
                url = f"{self.valves.S3_STORAGE_ENDPOINT}/{bucket}/{key}"

                # Generate signature for authentication (simplified for MinIO)
                async with httpx.AsyncClient(timeout=self.valves.AIHUB_REQUEST_TIMEOUT) as client:
                    response = await client.get(
                        url,
                        auth=(
                            self.valves.S3_STORAGE_ACCESS_KEY,
                            self.valves.S3_STORAGE_SECRET_KEY,
                        ),
                    )
                    response.raise_for_status()
                    return response.content

        except Exception as e:
            logger.exception(f"Error fetching file from S3: {e}")
            return None

    def _str_to_object_id(
        self, context_id: Annotated[Optional[str], "Context ID to hash"]
    ) -> Annotated[str, "ObjectId string"]:
        """
        Convert a string to an ObjectId by hashing it with MD5.
        """
        if not context_id:
            return str(ObjectId())
        hashed = hashlib.md5(context_id.encode()).digest()[:12]
        return str(ObjectId(hashed)).lower()

    async def pipes(self) -> list[dict]:
        """
        Fetch available conversational agents from AI-Hub.
        """
        if not self.valves.AIHUB_SUPERUSER_API_KEY:
            return [{"id": "error", "name": "API Key not configured"}]

        if not self.valves.OPEN_WEBUI_SIGNING_SECRET:
            return [{"id": "error", "name": "Signing secret not configured"}]

        try:
            headers = {
                "Authorization": f"Bearer {self.valves.AIHUB_SUPERUSER_API_KEY}",
                "Accept": "application/json",
            }

            async with httpx.AsyncClient(timeout=self.valves.AIHUB_REQUEST_TIMEOUT, follow_redirects=True) as client:
                response = await client.get(f"{self.valves.AIHUB_BASE_URL}/agents", headers=headers)
                response.raise_for_status()
                agents = response.json()

            # Filter for conversational agents that are online
            conversational_agents = []
            for agent in agents:
                if agent["is_conversational"] and agent["is_online"]:
                    conversational_agents.append(
                        {
                            "id": f"{agent['agent_class']}.{agent['agent_id']}",
                            "name": f"{self.valves.AIHUB_PIPELINE_PREFIX}{agent['agent_config']['name']}",
                        }
                    )

            if not conversational_agents:
                return [{"id": "error", "name": "No online conversational agents available"}]

            return conversational_agents

        except Exception as e:
            logger.exception(f"Error fetching agents: {e}")
            return [{"id": "error", "name": f"Error: {str(e)}"}]

    def _sign_user_headers(
        self,
        user_name: Annotated[str, "The user's name"],
        user_email: Annotated[str, "The user's email"],
    ) -> Annotated[str, "HMAC-SHA256 signature as hex string"]:
        """
        Sign user information with HMAC-SHA256 for authentication.
        """
        secret = self.valves.OPEN_WEBUI_SIGNING_SECRET.encode("utf-8")
        message = f"name:{user_name},email:{user_email}".encode()
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        return signature

    def _prepare_headers(
        self,
        user_name: Annotated[str, "User's name"],
        user_email: Annotated[str, "User's email"],
    ) -> Annotated[dict, "Request headers"]:
        """
        Prepare request headers with authentication and user information.
        """
        signature = self._sign_user_headers(user_name, user_email)

        return {
            "Authorization": f"Bearer {self.valves.AIHUB_SUPERUSER_API_KEY}",
            "Content-Type": "application/json",
            "X-OpenWebUI-User-Name": user_name,
            "X-OpenWebUI-User-Email": user_email,
            "X-OpenWebUI-Signature": signature,
        }

    def _convert_messages_to_event_format(
        self, messages: Annotated[list[dict], "List of messages from Open WebUI"]
    ) -> Annotated[list[dict], "List of messages in AI-Hub format"]:
        """
        Convert Open WebUI message format to AI-Hub UserMessageEvent format.
        Handles both simple string content and complex content with images.
        """
        converted_messages = []

        for msg in messages:
            content = msg.get("content")
            blocks = []

            # Handle different content types
            if isinstance(content, str):
                # Simple text message
                blocks = [{"block_type": "text", "text": content}]
            elif isinstance(content, list):
                # Complex content with potentially multiple blocks
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            blocks.append({"block_type": "text", "text": item.get("text", "")})
                        elif item.get("type") == "image_url":
                            # Handle image blocks - extract base64 data
                            image_url = item.get("image_url", {}).get("url", "")
                            if image_url.startswith("data:image"):
                                # Extract base64 data from data URL
                                try:
                                    # Format: data:image/png;base64,<data>
                                    parts = image_url.split(",", 1)
                                    if len(parts) == 2:
                                        header, base64_data = parts
                                        mime_type = header.split(";")[0].replace("data:", "")
                                        blocks.append(
                                            {
                                                "block_type": "image",
                                                "image_data": base64_data,
                                                "mime_type": mime_type,
                                            }
                                        )
                                except Exception as e:
                                    logger.warning(f"Failed to parse image URL: {e}")
                            else:
                                # Regular URL - just pass it through
                                blocks.append({"block_type": "image", "image_url": image_url})
                    elif isinstance(item, str):
                        # Fallback for string items in list
                        blocks.append({"block_type": "text", "text": item})
            elif isinstance(content, dict) and "blocks" in content:
                # Already in block format
                blocks = content["blocks"]
            else:
                # Fallback - try to convert to string
                blocks = [{"block_type": "text", "text": str(content) if content else ""}]

            converted_messages.append(
                {
                    "role": msg.get("role", "user"),
                    "blocks": blocks,
                    "additional_kwargs": {},
                }
            )

        return converted_messages

    async def _prepare_files_for_event(
        self, __files__: Annotated[Optional[list], "Files from Open WebUI"]
    ) -> Annotated[list[dict], "Files in AI-Hub format"]:
        """
        Convert Open WebUI files to AI-Hub event format by fetching from S3.
        """
        files_to_send = []

        if __files__:
            for file in __files__:
                try:
                    logger.debug(f"Processing file: {file.get('name', '')}, ID: {file.get('id', '')}")
                    file_id = file.get("id", "")
                    file_obj = Files.get_file_by_id(file_id)

                    if file_obj:
                        # Get file metadata
                        file_meta = file_obj.meta
                        filename = file_meta.get("name", "unnamed_file")
                        content_type = file_meta.get("content_type", "application/octet-stream")

                        # Fetch file from S3
                        s3_path = file_obj.path
                        logger.debug(f"Fetching file from S3: {s3_path}")

                        file_content = await self._fetch_file_from_s3(s3_path)

                        if file_content:
                            # Convert to base64
                            base64_data = base64.b64encode(file_content).decode("utf-8")

                            files_to_send.append(
                                {
                                    "filename": filename,
                                    "file_data": base64_data,
                                    "file_type": content_type,
                                }
                            )
                            logger.debug(f"Successfully prepared file: {filename}")
                        else:
                            logger.warning(f"Could not fetch file from S3: {s3_path}")
                    else:
                        logger.warning(f"Could not retrieve file with ID: {file_id}")

                except Exception as e:
                    logger.exception(f"Error processing file {file.get('name', '')}: {e}")

        return files_to_send

    def _build_endpoint_url(
        self,
        agent_class: Annotated[str, "Agent class identifier"],
        agent_id: Annotated[str, "Agent instance identifier"],
        event_name: Annotated[str, "Event name to send"],
        thread_id: Annotated[str, "Thread ID"],
        display_id: Annotated[str, "Display ID"],
    ) -> Annotated[str, "Complete endpoint URL"]:
        """
        Build the streaming endpoint URL for sending events to agents.
        """
        url = f"{self.valves.AIHUB_BASE_URL}/agents/{agent_class}/{agent_id}/{event_name}/stream"
        url += f"?thread_id={thread_id}&display_id={display_id}"
        return url

    async def _stream_agent_response(
        self,
        agent_class: Annotated[str, "Agent class identifier"],
        agent_id: Annotated[str, "Agent instance identifier"],
        event_name: Annotated[str, "Event name to send"],
        event_payload: Annotated[dict, "Event payload to send"],
        headers: Annotated[dict, "Request headers"],
        thread_id: Annotated[str, "Thread ID"],
        display_id: Annotated[str, "Display ID"],
        __event_emitter__: Annotated[Any, "Event emitter for streaming responses"],
        __event_call__: Annotated[Any, "Event caller for user interactions"],
        accumulated_content: Annotated[list, "List to accumulate content chunks"],
    ) -> None:
        """
        Stream an event to an agent and handle the SSE response.
        """
        endpoint_url = self._build_endpoint_url(agent_class, agent_id, event_name, thread_id, display_id)
        logger.debug(f"Streaming {event_name} to: {endpoint_url}")

        async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
            try:
                async with client.stream("POST", endpoint_url, json=event_payload, headers=headers) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        line = line.strip()

                        if line == "[DONE]":
                            logger.debug("Stream ended with [DONE]")
                            break

                        if not line:
                            continue

                        if line.startswith("data: "):
                            try:
                                json_str = line[6:]
                                if json_str == "[DONE]":
                                    logger.debug("Stream ended with data: [DONE]")
                                    break

                                event = json.loads(json_str)

                                # Process the event
                                should_continue = await self._process_event(
                                    event,
                                    __event_emitter__,
                                    __event_call__,
                                    accumulated_content,
                                    headers,
                                    agent_class,
                                    agent_id,
                                    thread_id,
                                )

                                if not should_continue:
                                    logger.debug(f"Stopping stream due to event: {event['_event_name']}")
                                    break

                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON: {e}, line: {line}")
                            except Exception as e:
                                logger.exception(f"Error processing event: {e}")

            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}"
                try:
                    error_detail = await e.response.aread()
                    error_msg = f"{error_msg}: {error_detail.decode()}"
                except:
                    pass

                logger.error(f"HTTP error: {error_msg}")
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "action": None,
                            "description": f"Connection error: {error_msg}",
                            "done": True,
                            "error": True,
                        },
                    }
                )
                await __event_emitter__(
                    {
                        "type": "chat:message:delta",
                        "data": {"content": f"\n\n> [!CAUTION]\n> {error_msg}\n"},
                    }
                )

            except Exception as e:
                logger.exception(f"Streaming error: {e}")
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "action": None,
                            "description": f"Error: {str(e)}",
                            "done": True,
                            "error": True,
                        },
                    }
                )
                await __event_emitter__(
                    {
                        "type": "chat:message:delta",
                        "data": {"content": f"\n\n> [!CAUTION]\n> {str(e)}\n"},
                    }
                )

    async def _process_event(
        self,
        event: Annotated[dict, "Event data"],
        __event_emitter__: Annotated[Any, "Event emitter"],
        __event_call__: Annotated[Any, "Event caller"],
        accumulated_content: Annotated[list, "Content accumulator"],
        headers: Annotated[dict, "Request headers"],
        agent_class: Annotated[str, "Agent class"],
        agent_id: Annotated[str, "Agent ID"],
        thread_id: Annotated[str, "Thread ID"],
    ) -> Annotated[bool, "Whether to continue processing"]:
        """
        Process an event and return whether to continue streaming.
        """
        parent_names = event.get("_parent_event_names", [])

        # Check event types in order of specificity
        if "ChunkEvent" in parent_names:
            # Handle ThoughtEvent with reasoning content
            reasoning_content = event.get("reasoning_content", "")
            regular_content = event.get("content", "")

            if reasoning_content:
                # Emit reasoning content to Open WebUI
                await __event_emitter__(
                    {
                        "type": "chat:completion",
                        "data": {
                            "choices": [
                                {
                                    "delta": {
                                        "content": regular_content,
                                        "thinking": reasoning_content,
                                    }
                                }
                            ],
                        },
                    }
                )
                logger.debug(f"Emitted reasoning: {reasoning_content[:100]}...")

            if regular_content:
                # Also handle regular content if present
                accumulated_content.append(regular_content)
                await __event_emitter__(
                    {
                        "type": "chat:message:delta",
                        "data": {"content": regular_content},
                    }
                )

            return True

        elif "ExceptionEvent" in parent_names:
            message = event.get("message", "An error occurred")
            error_content = f"\n\n> [!CAUTION]\n> {message}\n"

            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "action": None,
                        "description": f"Error: {message}",
                        "done": True,
                        "error": True,
                    },
                }
            )
            await __event_emitter__(
                {
                    "type": "chat:message:delta",
                    "data": {"content": error_content},
                }
            )

            accumulated_content.append(error_content)
            return False  # Stop processing

        elif "HumanInTheLoopRequestEvent" in parent_names:
            question = event.get("question", "Please provide input")
            topic = event.get("topic", {})

            logger.info(f"Received HITL request: {question}")

            # Get the response event name and IDs from the topic
            response_event_name = topic.get("event_name", "HumanInTheLoopResponseEvent")
            hitl_display_id = topic.get("display_id", "")

            # Prompt user for input
            result = await __event_call__(
                {
                    "type": "input",
                    "data": {
                        "title": "Agent Question",
                        "message": question,
                        "placeholder": "Enter your response...",
                    },
                }
            )

            user_response = result.get("value", "") if isinstance(result, dict) else str(result)

            if user_response:
                # Send the response back to the agent
                response_payload = {"response": user_response, "request_event": event}

                # Continue with the response event
                await self._stream_agent_response(
                    agent_class,
                    agent_id,
                    response_event_name,
                    response_payload,
                    headers,
                    thread_id,
                    hitl_display_id,  # Use HITL's display_id
                    __event_emitter__,
                    __event_call__,
                    accumulated_content,
                )

            return True  # Continue processing

        elif "DisplayEvent" in parent_names:
            # Generic display event handler
            display_description = event.get("display_description", {})
            event_description = display_description.get("en", "Processing...")

            logger.debug(f"Processing DisplayEvent: {event.get('_event_name', 'unknown')}")

            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "action": None,
                        "description": event_description,
                        "done": False,
                    },
                }
            )
            return True

        else:
            logger.warning(f"No handler for event: {event.get('_event_name', 'unknown')}")
            return True

    async def pipe(
        self,
        body: Annotated[dict, "Request body from Open WebUI"],
        __user__: Annotated[dict, "User information"],
        __metadata__: Annotated[dict, "Metadata from Open WebUI"],
        __event_emitter__: Annotated[Any, "Event emitter for streaming responses"],
        __event_call__: Annotated[Any, "Event caller for user interactions"],
        __files__: Annotated[Optional[list], "Files uploaded by the user"] = None,
        **kwargs,
    ) -> str:
        """
        Main entry point for the pipeline. Always streams.
        """
        # Extract agent info from model ID (format: pipe_id.agent_class.agent_id)
        model_id = body["model"]
        parts = model_id.split(".")

        if len(parts) < 3:
            logger.error(f"Invalid model ID format: {model_id}")
            return ""

        agent_class = parts[1]
        agent_id = ".".join(parts[2:])

        # Derive thread_id and display_id from Open WebUI metadata
        chat_id = __metadata__.get("chat_id")
        message_id = __metadata__.get("message_id")
        thread_id = self._str_to_object_id(chat_id)
        display_id = self._str_to_object_id(message_id)

        logger.debug(f"Processing request for {agent_class}.{agent_id}")
        logger.debug(f"Thread ID: {thread_id}, Display ID: {display_id}")

        # Prepare request
        headers = self._prepare_headers(__user__["name"], __user__["email"])
        messages = self._convert_messages_to_event_format(body["messages"])

        # Prepare files if any
        files = await self._prepare_files_for_event(__files__)

        # Build event payload
        event_payload = {
            "messages": messages,
        }

        # Add files if present
        if files:
            event_payload["files"] = files
            logger.debug(f"Attached {len(files)} file(s) to UserMessageEvent")

        accumulated_content = []

        # Emit initial status
        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "action": None,
                    "description": f"Connecting to agent {agent_class}.{agent_id}...",
                    "done": False,
                },
            }
        )

        # Stream UserMessageEvent to start the conversation
        await self._stream_agent_response(
            agent_class,
            agent_id,
            "UserMessageEvent",
            event_payload,
            headers,
            thread_id,
            display_id,
            __event_emitter__,
            __event_call__,
            accumulated_content,
        )

        # Emit final complete message
        if accumulated_content:
            complete_content = "".join(accumulated_content)
            await __event_emitter__(
                {
                    "type": "chat:message",
                    "data": {"content": complete_content},
                }
            )
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "action": None,
                        "description": "Response completed",
                        "done": True,
                    },
                }
            )
            logger.debug(f"Completed with {len(complete_content)} characters")

        return ""  # Content is sent via events
