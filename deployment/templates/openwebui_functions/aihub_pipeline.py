"""
AI-Hub Open-WebUI Pipeline - Server-Side Events Integration

This pipeline provides native integration between AI-Hub agents and Open-WebUI through
Server-Side Events (SSE) streaming. It translates AI-Hub's rich event system (thoughts,
tools, retrieval, human-in-the-loop) into Open-WebUI's native data structures.

Key Features:
- Event-driven architecture with Chain of Responsibility pattern
- Streaming content blocks (text, thinking, tool execution)
- Native AI-Hub event format preservation
- Automatic lifecycle management (streams auto-close with conversations)
- File upload support with S3/MinIO integration
- Human-in-the-loop interaction support

Architecture:
- EventHandler chain processes different AI-Hub event types
- StreamingStateManager maintains content block state
- ContentBlock hierarchy (TextBlock, ThinkingBlock, ToolBlock)
- SSE streaming to /api/v1/agents/classes/{class}/instances/{id}/{event}/stream endpoints
"""

import hashlib
import hmac
import html
import json
import logging
import os
import time
import urllib.parse
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Annotated, Optional, Protocol, Self, Callable
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field
from bson import ObjectId
from open_webui.models.files import Files
from opentelemetry.propagate import inject
from opentelemetry import trace

logger = logging.getLogger(__name__)


# ============================================================================
# Domain Models with Inheritance
# ============================================================================


class BlockType(StrEnum):
    TEXT = "text"
    THINKING = "thinking"
    TOOL = "tool"


class ContentBlock(BaseModel, ABC):
    """Abstract base class for all content blocks"""

    type: Annotated[BlockType, "The type of content block"]
    created_at: Annotated[float, "Unix timestamp when block was created"] = Field(default_factory=time.time)

    @abstractmethod
    def to_html(self) -> Annotated[str, "HTML representation of the block"]:
        """Convert block to HTML representation"""
        pass

    @abstractmethod
    def is_complete(self) -> Annotated[bool, "Whether the block is complete"]:
        """Check if the block is complete and ready to be finalized"""
        pass


class TextBlock(ContentBlock):
    """Block containing plain text content"""

    type: Annotated[BlockType, "Block type"] = Field(default=BlockType.TEXT, frozen=True)
    content: Annotated[str, "Text content of the block"] = ""

    def with_content(self, additional_content: Annotated[str, "Content to append"]) -> Self:
        """Return new block with appended content (immutable pattern)"""
        return self.model_copy(update={"content": self.content + additional_content})

    def to_html(self) -> Annotated[str, "HTML representation"]:
        """Convert to HTML - just return the text content"""
        return self.content

    def is_complete(self) -> Annotated[bool, "Always true for text blocks"]:
        """Text blocks are always ready to be finalized if they have content"""
        return bool(self.content)


class ThinkingBlock(ContentBlock):
    """Block containing AI reasoning/thinking content"""

    type: Annotated[BlockType, "Block type"] = Field(default=BlockType.THINKING, frozen=True)
    content: Annotated[str, "Reasoning content"] = ""
    closed: Annotated[bool, "Whether reasoning is complete"] = False
    ended_at: Annotated[Optional[float], "Unix timestamp when reasoning ended"] = None

    @property
    def duration(self) -> Annotated[Optional[int], "Duration in seconds"]:
        """Calculate duration of thinking in seconds"""
        if self.created_at and self.ended_at:
            return int(self.ended_at - self.created_at)
        return None

    def with_content(self, additional_content: Annotated[str, "Content to append"]) -> Self:
        """Return new block with appended content"""
        return self.model_copy(update={"content": self.content + additional_content})

    def with_closure(self) -> Self:
        """Return new closed block with end timestamp"""
        return self.model_copy(update={"closed": True, "ended_at": time.time()})

    def to_html(self) -> Annotated[str, "HTML details element"]:
        """Convert to HTML details element for reasoning display"""
        if self.closed and self.duration:
            return (
                f'\n<details type="reasoning" done="true" duration="{self.duration}">\n'
                f"{self.content.strip()}\n"
                f"</details>\n"
            )
        return f'\n<details type="reasoning" done="false">\n' f"{self.content.strip()}" f"</details>\n"

    def is_complete(self) -> Annotated[bool, "Whether block has content"]:
        """Thinking blocks are complete when they have content"""
        return bool(self.content)


class ToolBlock(ContentBlock):
    """Block representing tool/function execution"""

    type: Annotated[BlockType, "Block type"] = Field(default=BlockType.TOOL, frozen=True)
    tool_id: Annotated[str, "Unique identifier for the tool call"]
    tool_name: Annotated[str, "Name of the tool being called"]
    tool_params: Annotated[dict[str, Any], "Parameters passed to the tool"] = Field(default_factory=dict)
    closed: Annotated[bool, "Whether tool execution is complete"] = False
    ended_at: Annotated[Optional[float], "Unix timestamp when tool finished"] = None

    @property
    def duration(self) -> Annotated[Optional[int], "Execution duration in seconds"]:
        """Calculate tool execution duration"""
        if self.created_at and self.ended_at:
            return int(self.ended_at - self.created_at)
        return None

    def with_closure(self) -> Self:
        """Return new closed block"""
        return self.model_copy(update={"closed": True, "ended_at": time.time()})

    def to_html(self) -> Annotated[str, "HTML details element for tool"]:
        """Convert to HTML details element for tool display"""
        escaped_params = html.escape(json.dumps(self.tool_params))
        done_status = "true" if self.closed else "false"

        status_text = "Tool Executed" if self.closed else f"Calling {self.tool_name}..."

        return (
            f'\n<details type="tool_calls" done="{done_status}" id="{self.tool_id}" '
            f'name="{self.tool_name}" arguments="{escaped_params}">\n'
            f"<summary>{status_text}</summary>\n"
            f"</details>\n"
        )

    def is_complete(self) -> Annotated[bool, "Always true for tool blocks"]:
        """Tool blocks are always complete once created"""
        return True


# ============================================================================
# Factory for Creating Content Blocks
# ============================================================================


class ContentBlockFactory:
    """Factory for creating appropriate content block types"""

    @staticmethod
    def create_text_block(
        content: Annotated[str, "Initial text content"] = "",
    ) -> TextBlock:
        """Create a text content block"""
        return TextBlock(content=content)

    @staticmethod
    def create_thinking_block(
        content: Annotated[str, "Initial reasoning content"] = "",
    ) -> ThinkingBlock:
        """Create a thinking/reasoning block"""
        return ThinkingBlock(content=content)

    @staticmethod
    def create_tool_block(
        tool_id: Annotated[str, "Tool call ID"],
        tool_name: Annotated[str, "Tool name"],
        tool_params: Annotated[dict[str, Any], "Tool parameters"],
    ) -> ToolBlock:
        """Create a tool execution block"""
        return ToolBlock(tool_id=tool_id, tool_name=tool_name, tool_params=tool_params)


# ============================================================================
# Protocols for Dependency Injection
# ============================================================================


class EventEmitter(Protocol):
    """Protocol for event emission"""

    async def __call__(self, event: Annotated[dict[str, Any], "Event to emit"]) -> None: ...


class EventCaller(Protocol):
    """Protocol for event calling with response"""

    async def __call__(
        self, event: Annotated[dict[str, Any], "Event to call"]
    ) -> Annotated[dict[str, Any], "Response from event call"]: ...


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
        accept_language: Annotated[str | None, "Accept-Language header value"] = None,
    ) -> Annotated[dict[str, str], "HTTP headers with authentication"]:
        """Prepare authenticated request headers"""
        clean_username = urllib.parse.quote(user_name, safe="") if user_name else ""
        signature = self.sign_user_headers(clean_username, user_email)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-OpenWebUI-User-Name": clean_username,
            "X-OpenWebUI-User-Email": user_email,
            "X-OpenWebUI-Signature": signature,
        }
        if accept_language:
            headers["Accept-Language"] = accept_language
        return headers


# ============================================================================
# Message Conversion Service
# ============================================================================


class MessageConverter:
    """Handles message format conversions between Open WebUI and AI-Hub"""

    @staticmethod
    def convert_to_event_format(
        messages: Annotated[list[dict[str, Any]], "Open WebUI messages"],
    ) -> Annotated[list[dict[str, Any]], "AI-Hub formatted messages"]:
        """Convert Open WebUI messages to AI-Hub format"""
        converter = MessageConverter()
        return [converter._convert_single_message(msg) for msg in messages]

    def _convert_single_message(
        self, msg: Annotated[dict[str, Any], "Single message to convert"]
    ) -> Annotated[dict[str, Any], "Converted message"]:
        """Convert a single message"""
        content = msg.get("content")
        blocks = self._extract_blocks(content)

        return {
            "role": msg.get("role", "user"),
            "blocks": blocks,
            "additional_kwargs": {},
        }

    def _extract_blocks(
        self, content: Annotated[Any, "Content in various formats"]
    ) -> Annotated[list[dict[str, Any]], "List of content blocks"]:
        """Extract blocks from various content formats"""
        if isinstance(content, str):
            return [{"block_type": "text", "text": content}]
        elif isinstance(content, list):
            return self._extract_blocks_from_list(content)
        elif isinstance(content, dict) and "blocks" in content:
            return content["blocks"]
        else:
            return [{"block_type": "text", "text": str(content) if content else ""}]

    def _extract_blocks_from_list(
        self, content_list: Annotated[list[Any], "List of content items"]
    ) -> Annotated[list[dict[str, Any]], "Extracted blocks"]:
        """Extract blocks from list content"""
        blocks: list[dict[str, Any]] = []

        for item in content_list:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    blocks.append({"block_type": "text", "text": item.get("text", "")})
                elif item.get("type") == "image_url":
                    blocks.append(self._process_image_item(item))
            elif isinstance(item, str):
                blocks.append({"block_type": "text", "text": item})

        return blocks

    def _process_image_item(
        self, item: Annotated[dict[str, Any], "Image item to process"]
    ) -> Annotated[dict[str, Any], "Processed image block"]:
        """Process image items from content"""
        image_url = item.get("image_url", {}).get("url", "")

        # Pass the full data URL directly - LlamaIndex ImageBlock expects the url field
        # to contain either a regular URL or a data URL (data:image/...;base64,...)
        return {"block_type": "image", "url": image_url}


# ============================================================================
# Streaming State Management
# ============================================================================


class StreamingStateManager:
    """Manages streaming content state with proper encapsulation"""

    def __init__(self):
        self._content_blocks: Annotated[list[ContentBlock], "List of finalized content blocks"] = []
        self._current_block: Annotated[Optional[ContentBlock], "Currently active block being built"] = None
        self._block_factory = ContentBlockFactory()

    def start_text_block(self, content: Annotated[str, "Initial text content"] = "") -> None:
        """Start a new text block"""
        # Close any open blocks that need closing (tool or thinking)
        self._close_open_blocks()

        if self._current_block and isinstance(self._current_block, TextBlock):
            # Append to existing text block
            self._current_block = self._current_block.with_content(content)
        else:
            # Start new text block
            self._finalize_current_block()
            self._current_block = self._block_factory.create_text_block(content)

    def start_thinking_block(self, content: Annotated[str, "Initial reasoning content"] = "") -> None:
        """Start or append to thinking block"""
        # Close any open tool blocks
        self._close_tool_block_if_open()

        if self._current_block and isinstance(self._current_block, ThinkingBlock):
            # Append to existing thinking block
            self._current_block = self._current_block.with_content(content)
        else:
            # Start new thinking block
            self._finalize_current_block()
            self._current_block = self._block_factory.create_thinking_block(content)

    def start_tool_block(
        self,
        tool_id: Annotated[str, "Tool call identifier"],
        tool_name: Annotated[str, "Name of the tool"],
        tool_params: Annotated[dict[str, Any], "Tool parameters"],
    ) -> None:
        """Start a new tool execution block"""
        # Close any open blocks
        self._close_open_blocks()
        self._finalize_current_block()

        self._current_block = self._block_factory.create_tool_block(
            tool_id=tool_id, tool_name=tool_name, tool_params=tool_params
        )

    def append_to_current_block(self, content: Annotated[str, "Content to append"]) -> None:
        """Append content to current block if it supports it"""
        if self._current_block:
            if isinstance(self._current_block, (TextBlock, ThinkingBlock)):
                self._current_block = self._current_block.with_content(content)

    def close_current_block(self) -> None:
        """Close the current block if it supports closing"""
        if self._current_block:
            if isinstance(self._current_block, (ThinkingBlock, ToolBlock)):
                self._current_block = self._current_block.with_closure()
            self._finalize_current_block()

    def finalize_all_blocks(self) -> None:
        """Finalize all blocks when stream ends"""
        self._close_open_blocks()
        self._finalize_current_block()

    def _close_open_blocks(self) -> None:
        """Close any blocks that need closing (tool or thinking)"""
        if self._current_block:
            if isinstance(self._current_block, ToolBlock) and not self._current_block.closed:
                self._current_block = self._current_block.with_closure()
            elif isinstance(self._current_block, ThinkingBlock) and not self._current_block.closed:
                self._current_block = self._current_block.with_closure()

    def _close_tool_block_if_open(self) -> None:
        """Close tool block if it's currently open"""
        if self._current_block and isinstance(self._current_block, ToolBlock):
            if not self._current_block.closed:
                self._current_block = self._current_block.with_closure()
            self._finalize_current_block()

    def _finalize_current_block(self) -> None:
        """Move current block to finalized blocks if complete"""
        if self._current_block and self._current_block.is_complete():
            self._content_blocks.append(self._current_block)
            self._current_block = None

    def serialize_to_html(self) -> Annotated[str, "Complete HTML representation"]:
        """Serialize all blocks to HTML"""
        html_parts: list[str] = []

        # Render finalized blocks
        for block in self._content_blocks:
            html_parts.append(block.to_html())

        # Render current block if exists
        if self._current_block:
            html_parts.append(self._current_block.to_html())

        return "".join(html_parts)


# ============================================================================
# Event Handler Base Classes and Context
# ============================================================================


class EventContext:
    """Context object passed to event handlers"""

    def __init__(
        self,
        state_manager: Annotated[StreamingStateManager, "State manager instance"],
        emitter: Annotated[EventEmitter, "Event emitter function"],
        caller: Annotated[EventCaller, "Event caller function"],
        headers: Annotated[dict[str, str], "Request headers"],
        agent_class: Annotated[str, "Agent class identifier"],
        agent_id: Annotated[str, "Agent instance identifier"],
        thread_id: Annotated[str, "Thread identifier"],
        stream_service: Annotated[Any, "Streaming service instance"],
    ):
        self.state_manager = state_manager
        self.emitter = emitter
        self.caller = caller
        self.headers = headers
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.thread_id = thread_id
        self.stream_service = stream_service


class EventHandler(ABC):
    """Abstract base for event handlers in chain of responsibility"""

    def __init__(self):
        self._next_handler: Annotated[Optional[EventHandler], "Next handler in chain"] = None

    def set_next(
        self, handler: Annotated["EventHandler", "Next handler to chain"]
    ) -> Annotated["EventHandler", "The handler that was set"]:
        """Set the next handler in chain"""
        self._next_handler = handler
        return handler

    @abstractmethod
    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "Whether this handler can process the event"]:
        """Check if this handler can process the event"""
        pass

    @abstractmethod
    async def handle(
        self,
        event: Annotated[dict[str, Any], "Event to handle"],
        context: Annotated[EventContext, "Event processing context"],
    ) -> Annotated[bool, "Whether to continue processing"]:
        """Handle the event and return whether to continue"""
        pass

    async def process(
        self,
        event: Annotated[dict[str, Any], "Event to process"],
        context: Annotated[EventContext, "Event processing context"],
    ) -> Annotated[bool, "Whether to continue processing"]:
        """Process event through chain"""
        if await self.can_handle(event):
            return await self.handle(event, context)
        elif self._next_handler:
            return await self._next_handler.process(event, context)
        else:
            logger.warning(f"No handler for event: {event.get('_event_name', 'unknown')}")
            return True


# ============================================================================
# Concrete Event Handlers
# ============================================================================


class ThoughtEventHandler(EventHandler):
    """Handler for thought/reasoning events"""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if event contains ThoughtEvent"]:
        return "ThoughtEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Thought event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        reasoning_content = event.get("reasoning_content", "")
        context.state_manager.start_thinking_block(reasoning_content)

        await context.emitter(
            {
                "type": "replace",
                "data": {"content": context.state_manager.serialize_to_html()},
            }
        )
        return True


class ChunkEventHandler(EventHandler):
    """Handler for content chunk events"""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if event contains ChunkEvent"]:
        return "ChunkEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Chunk event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        content = event.get("content", "")
        context.state_manager.start_text_block(content)

        await context.emitter(
            {
                "type": "replace",
                "data": {"content": context.state_manager.serialize_to_html()},
            }
        )
        return True


class ToolEventHandler(EventHandler):
    """Handler for tool execution events"""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if event contains ToolEvent"]:
        return "ToolEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Tool event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        tool_name = event.get("name", "Unknown Tool")
        tool_description = event.get("description", "")
        parameters = event.get("parameters", {})
        tool_id = event.get("event_id", "")

        await context.emitter(
            {
                "type": "status",
                "data": {
                    "action": None,
                    "description": f"{tool_description}: {tool_name}",
                    "done": False,
                },
            }
        )

        context.state_manager.start_tool_block(tool_id=tool_id, tool_name=tool_name, tool_params=parameters)

        await context.emitter(
            {
                "type": "replace",
                "data": {"content": context.state_manager.serialize_to_html()},
            }
        )
        return True


class HumanInTheLoopHandler(EventHandler):
    """Handler for human-in-the-loop interactions.

    Supports three types of HITL events:
    - HumanInTheLoopConfirmationRequestEvent: Yes/No confirmation dialog (popup)
    - HumanInTheLoopInputRequestEvent: Free-form text input dialog (popup)
    - HumanInTheLoopChatRequestEvent: Chat-style input (appears as regular message)
    """

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if HITL request event"]:
        return "HumanInTheLoopRequestEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "HITL event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        question = event.get("question", "Please provide input")
        topic = event.get("topic", {})
        hitl_type = event.get("hitl_type", "input")

        logger.info(f"Received HITL request (type={hitl_type}): {question}")

        # Chat type: Display question as regular chat message, no popup
        # User will respond by typing a normal chat message
        if hitl_type == "chat":
            context.state_manager.start_text_block(f"\n\n{question}\n\n")
            await context.emitter(
                {
                    "type": "replace",
                    "data": {"content": context.state_manager.serialize_to_html()},
                }
            )
            # Don't send response here - it will come via the next user message
            return True

        if hitl_type == "confirmation":
            result = await context.caller(
                {
                    "type": "confirmation",
                    "data": {
                        "title": "Agent Question",
                        "message": question,
                    },
                }
            )
        else:
            result = await context.caller(
                {
                    "type": "input",
                    "data": {
                        "title": "Agent Question",
                        "message": question,
                        "placeholder": "Enter your response...",
                    },
                }
            )
            # Extract value from input result
            result = result.get("value", "") if isinstance(result, dict) else str(result)

        if result is not None and result != "":
            response_event_name = topic.get("event_name", "HumanInTheLoopResponseEvent")
            hitl_display_id = topic.get("display_id", "")
            agent_class = topic.get("agent_class", "")
            agent_id = topic.get("agent_id", "")

            response_payload = {"response": result, "request_event": event}

            await context.stream_service.send_hitl_response(
                response_event_name, response_payload, hitl_display_id, context, agent_class, agent_id
            )

        return True


class ExceptionEventHandler(EventHandler):
    """Handler for exception events"""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if exception event"]:
        return "ExceptionEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Exception event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Returns False to stop processing"]:
        context.state_manager.close_current_block()

        message = event.get("message", "An error occurred")
        error_content = f"\n\n> [!CAUTION]\n> {message}\n"

        context.state_manager.start_text_block(error_content)

        await context.emitter(
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

        await context.emitter(
            {
                "type": "replace",
                "data": {"content": context.state_manager.serialize_to_html()},
            }
        )

        return False


class EmbeddingEventHandler(EventHandler):
    """Handler for embedding/search events"""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if embedding event"]:
        return "EmbeddingEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Embedding event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        search_query = event.get("text", "")

        await context.emitter(
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


class RetrieverEventHandler(EventHandler):
    """Handler for document retrieval events"""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if retriever event"]:
        return "RetrieverEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Retriever event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        nodes = event.get("nodes", [])

        if nodes:
            for node in nodes:
                source_data = self._build_source_data(node)
                await context.emitter({"type": "source", "data": source_data})

            description = event.get("display_description", {}).get("en", f"Found {len(nodes)} relevant documents")

            await context.emitter(
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

    def _build_source_data(
        self, node: Annotated[dict[str, Any], "Node data"]
    ) -> Annotated[dict[str, Any], "Source data structure"]:
        """Build source data structure from node"""
        metadata = node.get("metadata", {})

        source_data = {
            "source": {
                "name": node.get("document_title", node.get("source", "Unknown Source")),
                "id": node.get("id", ""),
            },
            "document": [node.get("content", "")],
            "metadata": [
                {
                    "source": node.get("source", ""),
                    "document_title": node.get("document_title", ""),
                    "namespace": node.get("namespace", ""),
                    "language": node.get("language", ""),
                    "document_id": node.get("document_id", ""),
                    "reference_url": metadata.get("reference_url", ""),
                    "created_at": node.get("created_at", ""),
                    "name": node.get("source", ""),
                }
            ],
        }

        # Add optional fields
        if metadata.get("reference_url"):
            source_data["source"]["url"] = metadata["reference_url"]

        if node.get("index") is not None:
            source_data["metadata"][0]["page"] = node["index"]

        if "score" in node:
            source_data["distances"] = [node["score"]]

        return source_data


class RetrieveUserMemoryEventHandler(EventHandler):
    """Handler for user memory retrieval events"""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if event contains RetrieveUserMemoryEvent"]:
        return "RetrieveUserMemoryEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "User memory retrieval event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        memories = event.get("memories", [])

        if memories:
            for memory in memories:
                source_data = self._build_memory_source_data(memory, memory_type="user")
                await context.emitter({"type": "source", "data": source_data})

            description = event.get("display_description", {}).get("en", f"Retrieved {len(memories)} user memories")

            await context.emitter(
                {
                    "type": "status",
                    "data": {
                        "action": "memory_search",
                        "description": description,
                        "done": True,
                    },
                }
            )

        return True

    def _build_memory_source_data(
        self, memory: Annotated[dict[str, Any], "Memory data"], memory_type: Annotated[str, "Memory type"]
    ) -> Annotated[dict[str, Any], "Source data structure"]:
        """Build source data structure from memory"""
        metadata = memory.get("metadata", {})

        memory_id = memory.get("id", "")
        memory_text = memory.get("memory", "")
        score = memory.get("score")
        created_at = memory.get("created_at", "")

        source_data = {
            "source": {
                "name": f"💭 Memory: {memory_text[:100]}{'...' if len(memory_text) > 100 else ''}",
                "id": memory_id,
            },
            "document": [memory_text],
            "metadata": [
                {
                    "type": memory_type,
                    "memory_id": memory_id,
                    "created_at": created_at,
                    "user_id": metadata.get("user_id", ""),
                    "thread_id": metadata.get("thread_id", ""),
                    "agent_id": metadata.get("agent_id", ""),
                }
            ],
        }

        # Add relevance score if available
        if score is not None:
            source_data["distances"] = [score]

        return source_data


class RetrieveOrganizationMemoryEventHandler(EventHandler):
    """Handler for organization memory retrieval events"""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if event contains RetrieveOrganizationMemoryEvent"]:
        return "RetrieveOrganizationMemoryEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Organization memory retrieval event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        memories = event.get("memories", [])

        if memories:
            for memory in memories:
                source_data = self._build_memory_source_data(memory, memory_type="organization")
                await context.emitter({"type": "source", "data": source_data})

            description = event.get("display_description", {}).get(
                "en", f"Retrieved {len(memories)} organization memories"
            )

            await context.emitter(
                {
                    "type": "status",
                    "data": {
                        "action": "memory_search",
                        "description": description,
                        "done": True,
                    },
                }
            )

        return True

    def _build_memory_source_data(
        self, memory: Annotated[dict[str, Any], "Memory data"], memory_type: Annotated[str, "Memory type"]
    ) -> Annotated[dict[str, Any], "Source data structure"]:
        """Build source data structure from memory"""
        metadata = memory.get("metadata", {})

        memory_id = memory.get("id", "")
        memory_text = memory.get("memory", "")
        score = memory.get("score")
        created_at = memory.get("created_at", "")

        source_data = {
            "source": {
                "name": f"🏢 Org Memory: {memory_id[:8]}...",
                "id": memory_id,
            },
            "document": [memory_text],
            "metadata": [
                {
                    "type": memory_type,
                    "memory_id": memory_id,
                    "created_at": created_at,
                    "user_id": metadata.get("user_id", ""),
                    "thread_id": metadata.get("thread_id", ""),
                    "agent_id": metadata.get("agent_id", ""),
                    "tenant_id": metadata.get("tenant_id", ""),
                    "tenant_namespace": metadata.get("tenant_namespace", ""),
                }
            ],
        }

        # Add relevance score if available
        if score is not None:
            source_data["distances"] = [score]

        return source_data


class DefaultEventHandler(EventHandler):
    """Default handler for unrecognized display events"""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if display event"]:
        return "DisplayEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Display event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        display_description = event.get("display_description", {})
        event_description = display_description.get("en", "Processing...")

        logger.debug(f"Processing DisplayEvent: {event.get('_event_name', 'unknown')}")

        await context.emitter(
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


# ============================================================================
# Event Processing Factory
# ============================================================================


class EventProcessorFactory:
    """Factory for creating event processing chain"""

    @staticmethod
    def create_chain() -> Annotated[EventHandler, "First handler in chain"]:
        """Create the event processing chain of responsibility"""
        handlers = [
            ThoughtEventHandler(),
            ChunkEventHandler(),
            ToolEventHandler(),
            HumanInTheLoopHandler(),
            ExceptionEventHandler(),
            EmbeddingEventHandler(),
            RetrieverEventHandler(),
            RetrieveUserMemoryEventHandler(),
            RetrieveOrganizationMemoryEventHandler(),
            DefaultEventHandler(),
        ]

        # Link handlers in chain
        for i in range(len(handlers) - 1):
            handlers[i].set_next(handlers[i + 1])

        return handlers[0]


# ============================================================================
# Streaming Service
# ============================================================================


class StreamingService:
    """Manages streaming operations and SSE processing"""

    def __init__(
        self,
        base_url: Annotated[str, "AI-Hub base URL"],
        timeout: Annotated[int, "Request timeout in seconds"],
    ):
        self._base_url = base_url
        self._timeout = timeout
        self._event_processor = EventProcessorFactory.create_chain()

    def build_endpoint_url(
        self,
        agent_class: Annotated[str, "Agent class identifier"],
        agent_id: Annotated[str, "Agent instance identifier"],
        event_name: Annotated[str, "Event name to send"],
        thread_id: Annotated[str, "Thread identifier"],
        display_id: Annotated[str, "Display identifier"],
    ) -> Annotated[str, "Complete streaming endpoint URL"]:
        """Build streaming endpoint URL"""
        url = f"{self._base_url}/api/v1/agents/classes/{agent_class}/instances/{agent_id}/{event_name}/stream"
        url += f"?thread_id={thread_id}&display_id={display_id}"
        return url

    async def stream_response(
        self,
        agent_class: Annotated[str, "Agent class identifier"],
        agent_id: Annotated[str, "Agent instance identifier"],
        event_name: Annotated[str, "Event name to send"],
        event_payload: Annotated[dict[str, Any], "Event payload"],
        headers: Annotated[dict[str, str], "Request headers"],
        thread_id: Annotated[str, "Thread identifier"],
        display_id: Annotated[str, "Display identifier"],
        event_emitter: Annotated[EventEmitter, "Event emitter function"],
        event_caller: Annotated[EventCaller, "Event caller function"],
        state_manager: Annotated[StreamingStateManager, "State manager"],
        stream_start_callback: Annotated[Callable | None, "Stream start callback"] = None,
    ) -> None:
        """Stream an event and process responses"""
        endpoint_url = self.build_endpoint_url(agent_class, agent_id, event_name, thread_id, display_id)

        logger.debug(f"Streaming {event_name} to: {endpoint_url}")

        # Build context for event processing
        context = EventContext(
            state_manager=state_manager,
            emitter=event_emitter,
            caller=event_caller,
            headers=headers,
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            stream_service=self,
        )

        async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
            try:
                result = await self._process_stream(
                    client,
                    endpoint_url,
                    event_payload,
                    headers,
                    context,
                    stream_start_callback,
                )

                if result and result.get("type") == "error":
                    # HTTP error occurred - handle it
                    state_manager.finalize_all_blocks()
                    await self._handle_http_error_from_info(result, event_emitter)
                else:
                    # Finalize any open blocks when stream ends normally
                    state_manager.finalize_all_blocks()
                    # Emit final state if there were unclosed blocks
                    await event_emitter(
                        {
                            "type": "replace",
                            "data": {"content": state_manager.serialize_to_html()},
                        }
                    )

                    # Show usage warning if approaching limit
                    if result and result.get("type") == "usage_warning":
                        warning_msg = result.get("message", "Usage limit warning")
                        await event_emitter(
                            {
                                "type": "chat:message:delta",
                                "data": {"content": f"\n\n> [!WARNING]\n> {warning_msg}\n"},
                            }
                        )
            except Exception as e:
                state_manager.finalize_all_blocks()
                await self._handle_general_error(e, event_emitter)

    async def _process_stream(
        self,
        client: Annotated[httpx.AsyncClient, "HTTP client"],
        url: Annotated[str, "Endpoint URL"],
        payload: Annotated[dict[str, Any], "Request payload"],
        headers: Annotated[dict[str, str], "Request headers"],
        context: Annotated[EventContext, "Processing context"],
        stream_start_callback: Annotated[Callable | None, "Stream start callback"] = None,
    ) -> Annotated[dict[str, Any] | None, "Error info or usage warning info, None on success without warning"]:
        """Process the SSE stream. Returns dict with error or usage_warning info, None on plain success."""
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            # Check for error status codes before processing stream
            if response.status_code >= 400:
                # Read error body while still in context
                error_body = await response.aread()
                return {
                    "type": "error",
                    "status_code": response.status_code,
                    "body": error_body.decode(),
                }

            # Check for usage warning headers
            usage_warning = None
            if response.headers.get("X-Usage-Warning") == "true":
                usage_warning = {
                    "type": "usage_warning",
                    "message": response.headers.get("X-Usage-Warning-Message", "Usage limit warning"),
                }

            if stream_start_callback:
                await stream_start_callback()

            async for line in response.aiter_lines():
                if not await self._process_line(line, context):
                    break

        return usage_warning

    async def _process_line(
        self,
        line: Annotated[str, "SSE line to process"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Whether to continue processing"]:
        """Process a single SSE line"""
        line = line.strip()

        if line == "[DONE]":
            logger.debug("Stream ended with [DONE]")
            return False

        if not line or not line.startswith("data: "):
            return True

        try:
            json_str = line[6:]
            if json_str == "[DONE]":
                return False

            event = json.loads(json_str)
            return await self._event_processor.process(event, context)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}, line: {line}")
            return True
        except Exception as e:
            logger.exception(f"Error processing event: {e}")
            return True

    async def _handle_http_error_from_info(
        self,
        error_info: Annotated[dict[str, Any], "Error info with status_code and body"],
        emitter: Annotated[EventEmitter, "Event emitter"],
    ) -> None:
        """Handle HTTP errors using the pre-formatted message from the API response."""
        status_code = error_info["status_code"]
        error_body = error_info["body"]
        error_msg = f"HTTP {status_code}"

        logger.debug(f"HTTP {status_code} error body: {error_body}")

        try:
            error_data = json.loads(error_body)
            detail = error_data.get("detail", {})
            if isinstance(detail, dict) and detail.get("message"):
                error_msg = detail["message"]
            elif isinstance(detail, str):
                error_msg = detail
            else:
                error_msg = f"{error_msg}: {error_body}"
        except (json.JSONDecodeError, KeyError):
            error_msg = f"{error_msg}: {error_body}"

        logger.error(f"HTTP error: {error_msg}")

        await emitter(
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

        await emitter(
            {
                "type": "chat:message:delta",
                "data": {"content": f"\n\n> [!CAUTION]\n> {error_msg}\n"},
            }
        )

    async def _handle_general_error(
        self,
        error: Annotated[Exception, "General error"],
        emitter: Annotated[EventEmitter, "Event emitter"],
    ) -> None:
        """Handle general errors"""
        logger.exception(f"Streaming error: {error}")

        await emitter(
            {
                "type": "status",
                "data": {
                    "action": None,
                    "description": f"Error: {str(error)}",
                    "done": True,
                    "error": True,
                },
            }
        )

        await emitter(
            {
                "type": "chat:message:delta",
                "data": {"content": f"\n\n> [!CAUTION]\n> {str(error)}\n"},
            }
        )

    async def send_hitl_response(
        self,
        event_name: Annotated[str, "Response event name"],
        payload: Annotated[dict[str, Any], "Response payload"],
        display_id: Annotated[str, "HITL display ID"],
        context: Annotated[EventContext, "Original context"],
        agent_class: Annotated[str, "Agent class identifier"],
        agent_id: Annotated[str, "Agent instance identifier"],
    ) -> None:
        """Send HITL response back to agent"""
        await self.stream_response(
            agent_class,
            agent_id,
            event_name,
            payload,
            context.headers,
            context.thread_id,
            display_id,
            context.emitter,
            context.caller,
            context.state_manager,
        )


# ============================================================================
# Agent Discovery Service
# ============================================================================


class AgentDiscoveryService:
    """Service for discovering available agents"""

    def __init__(
        self,
        base_url: Annotated[str, "AI-Hub base URL"],
        api_key: Annotated[str, "API key"],
        prefix: Annotated[str, "UI prefix for agent names"],
        timeout: Annotated[int, "Request timeout"],
    ):
        self._base_url = base_url
        self._api_key = api_key
        self._prefix = prefix
        self._timeout = timeout

    async def discover_agents(
        self,
    ) -> Annotated[list[dict[str, str]], "List of available agents with id and name"]:
        """Fetch available conversational agents"""
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Accept": "application/json",
            }

            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(f"{self._base_url}/api/v1/agents/instances", headers=headers)
                response.raise_for_status()
                agents = response.json()

            return self._filter_conversational_agents(agents)

        except Exception as e:
            logger.exception(f"Error fetching agents: {e}")
            return [{"id": "error", "name": f"Error: {str(e)}"}]

    def _filter_conversational_agents(
        self, agents: Annotated[list[dict[str, Any]], "Raw agent data"]
    ) -> Annotated[list[dict[str, str]], "Filtered agent list"]:
        """Filter for online conversational agents"""
        conversational_agents: list[dict[str, str]] = []

        for agent in agents:
            if agent.get("is_conversational") and agent.get("is_online"):
                # Use name from config, fallback to agent_id if empty
                agent_config = agent.get("agent_config", {})
                display_name = agent_config.get("name", "No name Agent")
                conversational_agents.append(
                    {
                        "id": f"{agent['agent_class']}.{agent['agent_id']}",
                        "name": display_name,
                    }
                )

        if not conversational_agents:
            return [{"id": "error", "name": "No online conversational agents available"}]

        return conversational_agents


# ============================================================================
# File Processing Service
# ============================================================================


class FileProcessingService:
    """Handles file processing via the agent file upload API.

    Uploads files from OpenWebUI's S3 storage into the agent's dedicated
    bucket using the two-step initiate/validate flow, preventing IDOR.
    """

    def __init__(self, base_url: str, s3_endpoint: str, s3_access_key: str, s3_secret_key: str) -> None:
        self._base_url = base_url
        self._owui_s3_client = self._create_s3_client(s3_endpoint, s3_access_key, s3_secret_key)
        self._upload_cache: dict[str, dict[str, str]] = {}

    @staticmethod
    def _create_s3_client(endpoint: str, access_key: str, secret_key: str) -> Any:
        """Create a boto3 S3 client for reading files from OpenWebUI's storage."""
        import boto3
        from botocore.client import Config

        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

    async def prepare_files_for_event(
        self,
        files: Annotated[Optional[list[dict[str, Any]]], "Files from Open WebUI"],
        agent_class: Annotated[str, "Target agent class"],
        agent_id: Annotated[str, "Target agent instance ID"],
        headers: Annotated[dict[str, str], "Auth headers for AI-Hub API"],
    ) -> Annotated[list[dict[str, str]], "Prepared files for AI-Hub"]:
        """Upload Open WebUI files to the agent's bucket and return file references."""
        if not files:
            return []

        prepared_files: list[dict[str, str]] = []

        for file in files:
            owui_id = file.get("id", "")
            cache_key = f"{owui_id}:{agent_class}:{agent_id}"

            if cache_key in self._upload_cache:
                logger.debug(f"Using cached upload for file {file.get('name', '')} (owui_id={owui_id})")
                prepared_files.append(self._upload_cache[cache_key])
                continue

            try:
                prepared_file = await self._process_single_file(file, agent_class, agent_id, headers)
                if prepared_file:
                    self._upload_cache[cache_key] = prepared_file
                    prepared_files.append(prepared_file)
            except Exception as e:
                logger.exception(f"Error processing file {file.get('name', '')}: {e}")

        return prepared_files

    async def _process_single_file(
        self,
        file: Annotated[dict[str, Any], "Single file to process"],
        agent_class: Annotated[str, "Target agent class"],
        agent_id: Annotated[str, "Target agent instance ID"],
        headers: Annotated[dict[str, str], "Auth headers"],
    ) -> Annotated[Optional[dict[str, str]], "Processed file or None"]:
        """Upload a single file to the agent's bucket via initiate → PUT → validate."""
        logger.debug(f"Processing file: {file.get('name', '')}, ID: {file.get('id', '')}")

        owui_file_id = file.get("id", "")
        file_obj = Files.get_file_by_id(owui_file_id)

        if not file_obj:
            logger.warning(f"Could not retrieve file with ID: {owui_file_id}")
            return None

        file_meta = file_obj.meta
        filename = file_meta.get("name", "unnamed_file")
        content_type = file_meta.get("content_type", "application/octet-stream")

        # Read file content from OpenWebUI's S3 storage
        file_content = self._read_file_content(file_obj)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Initiate upload — get presigned URL + file_id
            initiate_url = (
                f"{self._base_url}/api/v1/agents/classes/{agent_class}/instances/{agent_id}/files/upload/initiate"
            )
            initiate_resp = await client.post(
                initiate_url,
                headers=headers,
                json={"filename": filename, "content_type": content_type},
            )
            initiate_resp.raise_for_status()
            initiate_data = initiate_resp.json()

            upload_url = initiate_data["upload_url"]
            agent_file_id = initiate_data["file_id"]

            # Step 2: PUT file content to presigned URL
            put_resp = await client.put(
                upload_url,
                content=file_content,
                headers={"Content-Type": content_type},
            )
            put_resp.raise_for_status()

            # Step 3: Validate upload
            validate_url = (
                f"{self._base_url}/api/v1/agents/classes/{agent_class}/instances/{agent_id}/files/upload/validate"
            )
            validate_resp = await client.post(
                validate_url,
                headers=headers,
                json={"file_id": agent_file_id, "filename": filename},
            )
            validate_resp.raise_for_status()
            validate_data = validate_resp.json()

            if not validate_data.get("exists"):
                logger.warning(f"File validation failed for {filename} (file_id={agent_file_id})")
                return None

        logger.debug(f"Successfully uploaded file: {filename} -> file_id={agent_file_id}")

        return {
            "filename": filename,
            "file_type": content_type,
            "file_id": agent_file_id,
        }

    def _read_file_content(self, file_obj: Any) -> bytes:
        """Read file content from OpenWebUI's S3 storage."""
        parsed = urlparse(file_obj.path)
        if parsed.scheme != "s3":
            raise ValueError(f"Unsupported storage path scheme: {file_obj.path}")

        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        response = self._owui_s3_client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()


# ============================================================================
# Main Pipeline Facade
# ============================================================================


class Pipe:
    """
    AI-Hub Agent Connector Pipeline - Main Facade

    This is the entry point that orchestrates all services using the Facade pattern.
    """

    class Valves(BaseModel):
        """Configuration valves for the pipeline"""

        AIHUB_BASE_URL: str = Field(
            default=os.getenv("AIHUB_BASE_URL", "http://localhost:8000"),
            description="Base URL for the AI-Hub API endpoints",
        )
        AIHUB_FRONTEND_URL: str = Field(
            default=os.getenv("AIHUB_FRONTEND_URL", "http://localhost:3333"),
            description="Base URL for the AI-Hub frontend",
        )
        AIHUB_SUPERUSER_API_KEY: str = Field(
            default=os.getenv("AIHUB_SUPERUSER_API_KEY", ""),
            description="API key for authenticating with AI-Hub",
        )
        OPEN_WEBUI_SIGNING_SECRET: str = Field(
            default=os.getenv("OPEN_WEBUI_SIGNING_SECRET", ""),
            description="Secret key for signing user headers",
        )
        AIHUB_PIPELINE_PREFIX: str = Field(
            default=os.getenv("AIHUB_PIPELINE_PREFIX", "agent/"),
            description="Prefix added to agent names in the UI",
        )
        AIHUB_REQUEST_TIMEOUT: int = Field(
            default=int(os.getenv("AIHUB_REQUEST_TIMEOUT", "60")),
            description="Request timeout in seconds",
        )
        S3_STORAGE_ENDPOINT: str = Field(
            default=os.getenv("S3_ENDPOINT_URL", ""),
            description="S3/MinIO endpoint URL for reading OpenWebUI files",
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
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize all required services"""
        # Authentication
        self._auth_service = AuthenticationService(
            self.valves.OPEN_WEBUI_SIGNING_SECRET, self.valves.AIHUB_SUPERUSER_API_KEY
        )

        # File Processing
        self._file_service = FileProcessingService(
            self.valves.AIHUB_BASE_URL,
            self.valves.S3_STORAGE_ENDPOINT,
            self.valves.S3_STORAGE_ACCESS_KEY,
            self.valves.S3_STORAGE_SECRET_KEY,
        )

        # Message Conversion
        self._message_converter = MessageConverter()

        # Agent Discovery
        self._agent_discovery = AgentDiscoveryService(
            self.valves.AIHUB_BASE_URL,
            self.valves.AIHUB_SUPERUSER_API_KEY,
            self.valves.AIHUB_PIPELINE_PREFIX,
            self.valves.AIHUB_REQUEST_TIMEOUT,
        )

        # Streaming
        self._streaming_service = StreamingService(self.valves.AIHUB_BASE_URL, self.valves.AIHUB_REQUEST_TIMEOUT)

    async def pipes(
        self,
    ) -> Annotated[list[dict[str, str]], "List of available agent pipelines"]:
        """Discover available agents"""
        if not self._validate_configuration():
            return [{"id": "error", "name": "Configuration incomplete"}]

        return await self._agent_discovery.discover_agents()

    def _validate_configuration(self) -> Annotated[bool, "Configuration validity"]:
        """Validate required configuration"""
        return bool(self.valves.AIHUB_SUPERUSER_API_KEY and self.valves.OPEN_WEBUI_SIGNING_SECRET)

    def _extract_agent_info(
        self, model_id: Annotated[str, "Model ID from request"]
    ) -> Annotated[tuple[str, str], "Agent class and ID"]:
        """Extract agent class and ID from model ID"""
        parts = model_id.split(".")
        if len(parts) < 3:
            raise ValueError(f"Invalid model ID format: {model_id}")

        agent_class = parts[1]
        agent_id = ".".join(parts[2:])
        return agent_class, agent_id

    def _generate_ids(
        self,
        chat_id: Annotated[Optional[str], "Chat session ID"],
        message_id: Annotated[Optional[str], "Message ID"],
    ) -> Annotated[tuple[str, str], "Thread and display IDs"]:
        """Generate thread and display IDs"""
        thread_id = self._str_to_object_id(chat_id)
        display_id = self._str_to_object_id(message_id)
        return thread_id, display_id

    def _str_to_object_id(
        self, context_id: Annotated[Optional[str], "Context ID to convert"]
    ) -> Annotated[str, "ObjectId string"]:
        """Convert string to ObjectId format"""
        if not context_id:
            return str(ObjectId())
        hashed = hashlib.md5(context_id.encode()).digest()[:12]
        return str(ObjectId(hashed)).lower()

    async def _set_ui_context(
        self,
        thread_id: Annotated[str, "Thread ID"],
        display_id: Annotated[str, "Display ID"],
        event_caller: Annotated[EventCaller, "Event caller function"],
    ) -> None:
        """Emit JavaScript to show trace viewer"""
        code = f"""
        window.parent.postMessage({{
            type: 'set-context',
            thread_id: '{thread_id}',
            display_id: '{display_id}',
        }}, '{self.valves.AIHUB_FRONTEND_URL}');
        """

        await event_caller({"type": "execute", "data": {"code": code}})

    async def _check_open_chat_hitl(
        self,
        thread_id: Annotated[str, "Thread ID"],
        headers: Annotated[dict[str, str], "Request headers"],
    ) -> Annotated[dict[str, Any] | None, "Open chat HITL request or None"]:
        """Query API for open chat HITL in this thread."""
        try:
            async with httpx.AsyncClient(timeout=self.valves.AIHUB_REQUEST_TIMEOUT) as client:
                response = await client.get(
                    f"{self.valves.AIHUB_BASE_URL}/api/v1/threads/{thread_id}/open-chat-hitl",
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("has_open_chat_hitl"):
                        return data["hitl_request"]
        except Exception as e:
            logger.warning(f"Failed to check open chat HITL: {e}")
        return None

    async def pipe(
        self,
        body: Annotated[dict[str, Any], "Request body"],
        __user__: Annotated[dict[str, str], "User information"],
        __metadata__: Annotated[dict[str, str], "Request metadata"],
        __event_emitter__: Annotated[Any, "Event emitter function"],
        __event_call__: Annotated[Any, "Event caller function"],
        __request__: Annotated[Any, "HTTP request object"] = None,
        __files__: Annotated[Optional[list[dict[str, Any]]], "Uploaded files"] = None,
        **kwargs,
    ) -> Annotated[str, "Response (always empty for streaming)"]:
        """Main pipeline entry point"""
        # Extract agent information
        agent_class, agent_id = self._extract_agent_info(body["model"])

        # Generate IDs
        thread_id, display_id = self._generate_ids(__metadata__.get("chat_id"), __metadata__.get("message_id"))

        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            f"Pipeline {agent_class}.{agent_id}",
            attributes={
                "agent.class": agent_class,
                "agent.id": agent_id,
                "thread.id": thread_id,
                "user.email": __user__["email"],
            },
        ) as span:
            try:
                logger.debug(f"Processing request for {agent_class}.{agent_id}")
                logger.debug(f"Thread ID: {thread_id}, Display ID: {display_id}")

                # Prepare authentication (forward Accept-Language for localized error messages)
                accept_language = __request__.headers.get("Accept-Language") if __request__ else None
                headers = self._auth_service.prepare_headers(__user__["name"], __user__["email"], accept_language)
                inject(headers)

                # Convert messages
                messages = self._message_converter.convert_to_event_format(body["messages"])

                # Process files — upload to agent's dedicated bucket
                files = await self._file_service.prepare_files_for_event(
                    __files__, agent_class, agent_id, headers
                )

                # Check for open chat HITL - if found, send HITL response instead of UserMessageEvent
                open_hitl = await self._check_open_chat_hitl(thread_id, headers)

                if open_hitl:
                    # Route as HITL response
                    topic = open_hitl.get("topic", {})
                    event_name = topic.get("event_name", "HumanInTheLoopChatResponseEvent")
                    hitl_display_id = topic.get("display_id", display_id)
                    # Use the user's message content as the response
                    # Note: messages have been converted to blocks format, so extract text from there
                    user_message_content = ""
                    if messages:
                        blocks = messages[-1].get("blocks", [])
                        if blocks:
                            user_message_content = blocks[0].get("text", "")
                    event_payload = {
                        "response": user_message_content,
                        "request_event": open_hitl,
                    }
                    logger.info(f"Routing user message as chat HITL response for event: {event_name}")
                else:
                    # Normal flow - send UserMessageEvent
                    event_name = "UserMessageEvent"
                    hitl_display_id = display_id
                    event_payload = {"messages": messages}
                    if files:
                        event_payload["files"] = files
                        logger.debug(f"Attached {len(files)} file(s) to UserMessageEvent")

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

                state_manager = StreamingStateManager()

                async def stream_start_callback():
                    await self._set_ui_context(thread_id, hitl_display_id, __event_call__)

                # Stream the conversation
                await self._streaming_service.stream_response(
                    agent_class,
                    agent_id,
                    event_name,
                    event_payload,
                    headers,
                    thread_id,
                    hitl_display_id,
                    __event_emitter__,
                    __event_call__,
                    state_manager,
                    stream_start_callback,
                )

                # Emit completion status
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

                logger.debug("Request processing completed")
                return ""

            except Exception as e:
                logger.exception(f"Error in pipe: {e}")
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "action": None,
                            "description": f"Pipeline error: {str(e)}",
                            "done": True,
                            "error": True,
                        },
                    }
                )
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return f"Error: {str(e)}"
