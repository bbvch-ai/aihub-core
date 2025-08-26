"""
title: AI-Hub Agent Connector
description: Connects Open WebUI to AI-Hub agents with streaming support
author: AI-Hub Team
version: 1.0.0
required_open_webui_version: 0.6.0
"""

import base64
import hashlib
import hmac
import html
import json
import logging
import os
from enum import Enum

import time
from typing import Any, Annotated, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field
from bson import ObjectId
import boto3
from botocore.client import Config
from open_webui.models.files import Files

logger = logging.getLogger(__name__)


class BlockType(str, Enum):
    TEXT = "text"
    THINKING = "thinking"
    TOOL = "tool"  # New block type for tool calls


class ContentBlock(BaseModel):
    type: BlockType
    content: str = ""
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    closed: bool = False
    # Additional fields for tool blocks
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_params: Optional[dict] = None
    tool_result: Optional[str] = None

    @property
    def duration(self) -> Optional[int]:
        if self.started_at and self.ended_at:
            return int(self.ended_at - self.started_at)
        return None

    def close(self):
        """Close the block and set end time"""
        self.closed = True
        self.ended_at = time.time()

    def append_content(self, content: str):
        """Append content to this block"""
        self.content += content

    def to_html(self) -> str:
        """Convert block to HTML representation"""
        if self.type == BlockType.THINKING:
            if self.closed and self.duration:
                return (
                    f'\n<details type="reasoning" done="true" duration="{self.duration}">\n'
                    f"{self.content.strip()}\n"
                    f"</details>\n"
                )
            else:
                return f'\n<details type="reasoning" done="false">\n' f"{self.content.strip()}" f"</details>\n"
        elif self.type == BlockType.TOOL:
            escaped_params = html.escape(json.dumps(self.tool_params or {}))
            done_status = "true" if self.closed else "false"

            result_attr = ""
            if self.tool_result and self.closed:
                escaped_result = html.escape(json.dumps(self.tool_result))
                result_attr = f' result="{escaped_result}"'

            return (
                f'\n<details type="tool_calls" done="{done_status}" id="{self.tool_id}" '
                f'name="{self.tool_name}" arguments="{escaped_params}"{result_attr}>\n'
                f'<summary>{"Tool Executed" if self.closed else f"Calling {self.tool_name}..."}</summary>\n'
                f"</details>\n"
            )
        else:  # TEXT
            return self.content


class StreamingState(BaseModel):
    """State management for streaming content"""

    content_blocks: list[ContentBlock] = Field(default_factory=list)
    current_block: Optional[ContentBlock] = None

    def close_tool_blocks(self) -> None:
        """Close any open tool blocks"""
        if self.current_block and self.current_block.type == BlockType.TOOL and not self.current_block.closed:
            self.current_block.close()
            self.finalize_current_block()

    def start_tool_block(self, tool_id: str, tool_name: str, tool_params: dict) -> None:
        """Start a new tool block"""
        # Close any existing tool blocks
        self.close_tool_blocks()

        # Finalize current block if it's not a tool
        if self.current_block and self.current_block.type != BlockType.TOOL:
            self.finalize_current_block()

        self.current_block = ContentBlock(
            type=BlockType.TOOL, tool_id=tool_id, tool_name=tool_name, tool_params=tool_params, started_at=time.time()
        )

    def start_thinking_block(self, content: str = "") -> None:
        """Start or append to a thinking block"""
        # Close any open tool blocks
        self.close_tool_blocks()

        if self.current_block and self.current_block.type == BlockType.THINKING:
            # Already in thinking block, just append
            self.current_block.append_content(content)
        else:
            # Close current block if exists and start new thinking block
            self.finalize_current_block()
            self.current_block = ContentBlock(type=BlockType.THINKING, content=content, started_at=time.time())

    def start_text_block(self, content: str = "") -> None:
        """Start or append to a text block"""
        # Close any open tool blocks
        self.close_tool_blocks()

        # If we were thinking, close that block
        if self.current_block and self.current_block.type == BlockType.THINKING:
            self.current_block.close()
            self.finalize_current_block()

        if self.current_block and self.current_block.type == BlockType.TEXT:
            # Already in text block, just append
            self.current_block.append_content(content)
        else:
            # Start new text block
            self.finalize_current_block()
            self.current_block = ContentBlock(type=BlockType.TEXT, content=content)

    def finalize_current_block(self) -> None:
        """Move current block to content_blocks if it exists"""
        if self.current_block and (self.current_block.content or self.current_block.type == BlockType.TOOL):
            self.content_blocks.append(self.current_block)
            self.current_block = None

    def serialize_to_html(self) -> str:
        """Serialize all content blocks to HTML"""
        html_parts = []

        # Add all finalized blocks
        for block in self.content_blocks:
            html_parts.append(block.to_html())

        # Add current block if exists
        if self.current_block:
            html_parts.append(self.current_block.to_html())

        return "".join(html_parts)


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
            default=os.getenv("AIHUB_BASE_URL", "http://localhost:8000"),
            description="Base URL for the AI-Hub API endpoints (without /api/v1)",
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
        """Fetch a file from S3/MinIO storage."""
        # Parse S3 path
        parsed = urlparse(s3_path)
        if parsed.scheme != "s3":
            logger.error(f"Invalid S3 path: {s3_path}")
            return None

        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        # Create S3 client
        s3_client = boto3.client(
            "s3",
            endpoint_url=self.valves.S3_STORAGE_ENDPOINT,
            aws_access_key_id=self.valves.S3_STORAGE_ACCESS_KEY,
            aws_secret_access_key=self.valves.S3_STORAGE_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

        # Download file
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def _str_to_object_id(
        self, context_id: Annotated[Optional[str], "Context ID to hash"]
    ) -> Annotated[str, "ObjectId string"]:
        """Convert a string to an ObjectId by hashing it with MD5."""
        if not context_id:
            return str(ObjectId())
        hashed = hashlib.md5(context_id.encode()).digest()[:12]
        return str(ObjectId(hashed)).lower()

    async def pipes(self) -> list[dict]:
        """Fetch available conversational agents from AI-Hub."""
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
                response = await client.get(f"{self.valves.AIHUB_BASE_URL}/api/v1/agents", headers=headers)
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
        """Sign user information with HMAC-SHA256 for authentication."""
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
        if not __files__:
            return []

        files_to_send = []

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
        url = f"{self.valves.AIHUB_BASE_URL}/api/v1/agents/{agent_class}/{agent_id}/{event_name}/stream"
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
        state: Annotated[StreamingState, "State object for accumulation"],
    ) -> None:
        """
        Stream an event to an agent and handle the SSE response.
        """
        endpoint_url = self._build_endpoint_url(agent_class, agent_id, event_name, thread_id, display_id)
        logger.debug(f"Streaming {event_name} to: {endpoint_url}")

        # Initialize state for content accumulation

        async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
            try:
                async with client.stream("POST", endpoint_url, json=event_payload, headers=headers) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        line = line.strip()

                        if line == "[DONE]":
                            logger.debug("Stream ended with [DONE]")
                            break

                        if not line or not line.startswith("data: "):
                            continue

                        try:
                            json_str = line[6:]
                            if json_str == "[DONE]":
                                break

                            event = json.loads(json_str)

                            # Process the event with state
                            should_continue = await self._process_event(
                                event,
                                __event_emitter__,
                                __event_call__,
                                headers,
                                agent_class,
                                agent_id,
                                thread_id,
                                state,
                            )

                            if not should_continue:
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
        headers: Annotated[dict, "Request headers"],
        agent_class: Annotated[str, "Agent class"],
        agent_id: Annotated[str, "Agent ID"],
        thread_id: Annotated[str, "Thread ID"],
        state: Annotated[StreamingState, "State object for accumulation"],
    ) -> Annotated[bool, "Whether to continue processing"]:
        """
        Process an event and return whether to continue streaming.
        """
        parent_names = event.get("_parent_event_names", [])

        # Handle ThoughtEvent
        if "ThoughtEvent" in parent_names:
            reasoning_content = event.get("reasoning_content", "")
            state.start_thinking_block(reasoning_content)

            # Emit full message
            await __event_emitter__(
                {
                    "type": "replace",
                    "data": {
                        "content": state.serialize_to_html(),
                    },
                }
            )
            return True

        # Handle ChunkEvent
        if "ChunkEvent" in parent_names:
            regular_content = event.get("content", "")
            state.start_text_block(regular_content)

            # Emit full message
            await __event_emitter__(
                {
                    "type": "replace",
                    "data": {
                        "content": state.serialize_to_html(),
                    },
                }
            )
            return True

        if "EmbeddingEvent" in parent_names:
            search_query = event.get("text", "")

            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "action": "knowledge_search",
                        "query": search_query,
                        "done": True,
                        "error": False,
                    },
                }
            )
            return True

        if "RetrieverEvent" in parent_names:
            nodes = event.get("nodes", [])

            if nodes:
                # Emit each node as a separate source event
                for node in nodes:
                    # Prepare the source data structure
                    source_data = {
                        "source": {
                            "name": node.get("document_title", node.get("source", "Unknown Source")),
                            "id": node.get("id", ""),
                            # Add URL if reference_url exists
                            **(
                                {"url": node.get("metadata", {}).get("reference_url")}
                                if node.get("metadata", {}).get("reference_url")
                                else {}
                            ),
                        },
                        "document": [node.get("content", "")],
                        "metadata": [
                            {
                                "source": node.get("source", ""),
                                "document_title": node.get("document_title", ""),
                                "namespace": node.get("namespace", ""),
                                "language": node.get("language", ""),
                                "document_id": node.get("document_id", ""),
                                "reference_url": node.get("metadata", {}).get("reference_url", ""),
                                "created_at": node.get("created_at", ""),
                                # Add file-related metadata if available
                                "name": node.get("source", ""),  # File name for display
                                # Page number if available (subtract 1 since frontend adds 1)
                                **({"page": node.get("index", 0)} if node.get("index") is not None else {}),
                            }
                        ],
                        # Add distance/score for relevance display
                        **({"distances": [node.get("score", 0.0)]} if "score" in node else {}),
                    }

                    # Emit as a source event
                    await __event_emitter__(
                        {"type": "source", "data": source_data}  # This gets handled by chatEventHandler
                    )

                # Emit status to show retrieval completion
                display_description = event.get("display_description", {})
                description = display_description.get("en", f"Found {len(nodes)} relevant documents")

                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "action": None,
                            "description": description,
                            "done": True,
                        },
                    }
                )

            return True

        # Handle ToolEvent - Display tool usage
        if "ToolEvent" in parent_names:
            tool_name = event.get("name", "Unknown Tool")
            tool_description = event.get("description", "")
            parameters = event.get("parameters", {})
            tool_id = event.get("event_id")

            # Emit status event to show tool is being called
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "action": None,
                        "description": f"{tool_description}: {tool_name}",
                        "done": False,
                    },
                }
            )

            # Start a tool block
            state.start_tool_block(tool_id=tool_id, tool_name=tool_name, tool_params=parameters)

            # Emit the updated content
            await __event_emitter__(
                {
                    "type": "replace",
                    "data": {
                        "content": state.serialize_to_html(),
                    },
                }
            )

            return True

        if "ExceptionEvent" in parent_names:
            # Finalize any open blocks
            state.finalize_current_block()

            message = event.get("message", "An error occurred")
            error_content = f"\n\n> [!CAUTION]\n> {message}\n"

            # Add error as text block
            state.start_text_block(error_content)

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
                    "type": "replace",
                    "data": {"content": state.serialize_to_html()},
                }
            )
            return False

        if "HumanInTheLoopRequestEvent" in parent_names:
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
                    state,
                )

            return True  # Continue processing

        if "DisplayEvent" in parent_names:
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

        code = f"""
        window.parent.postMessage({{
            type: 'show-traces',
            thread_id: '{thread_id}',
            display_id: '{display_id}',
          }}, '{self.valves.AIHUB_BASE_URL}');
        """

        await __event_call__(
            {
                "type": "execute",
                "data": {
                    "code": code,
                },
            }
        )

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
            state=StreamingState(),
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
        logger.debug("Completed")

        return ""
