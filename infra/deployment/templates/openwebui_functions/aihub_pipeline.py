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
- SSE streaming to /api/v1/active/agents/classes/{class}/instances/{id}/{event}/stream endpoints
"""

import asyncio
import hashlib
import hmac
import html
import json
import logging
import os
import re
import secrets
import time
import urllib.parse
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from enum import StrEnum
from typing import Any, Annotated, Optional, Protocol, Self, Callable
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field
from open_webui.models.chats import Chats
from open_webui.models.files import Files
from open_webui.models.users import Users
from open_webui.utils.chat_id import is_saved_chat_id
from opentelemetry.propagate import inject
from opentelemetry import trace

logger = logging.getLogger(__name__)

# Redis key under which the pipeline stashes the agent-produced conversation title so the
# ``aihub_title_filter`` outlet can re-apply it AFTER OpenWebUI's first-turn title fallback overwrites
# the chat title with the user's prompt. Must stay in sync with the key in ``aihub_title_filter.py``.
AIHUB_TITLE_REDIS_KEY = "aihub:title:{chat_id}"
AIHUB_TITLE_REDIS_TTL_SECONDS = 600

# Must stay in sync with ``aihub_feature_filter.py``, which stashes the chat features the selected agent supports
# under this key before OpenWebUI would act on them.
REQUESTED_FEATURES_METADATA_KEY = "aihub_requested_features"

# The type Open WebUI gives a knowledge entry the user referenced with `#`. Ours hold no content: each stands for one
# of our collections, which the agent searches itself.
KNOWLEDGE_COLLECTION_TYPE = "collection"

# OpenWebUI file meta key under which the pipe remembers each agent's upload of that file, keyed "{class}/{id}", so
# a file forwarded again on a later turn is not copied into the agent bucket a second time.
AGENT_UPLOADS_FILE_META_KEY = "aihub_agent_uploads"

# Must stay in sync with the filename limit of the API's ``AgentFileUploadRequest``.
AGENT_UPLOAD_FILENAME_MAX_LENGTH = 255

# A temporary chat's text item, a note and an attached chat have no file in Open WebUI, so the pipe remembers the agent's
# upload of each, by the item's id (a note's or chat's with its version), in Open WebUI's Redis; for as long as the
# agent-files bucket keeps it.
# A temporary chat's id comes from the browser, so the key also names the user the upload belongs to.
AIHUB_TEMPORARY_UPLOAD_REDIS_KEY = "aihub:temp-upload:{user_id}:{thread_id}:{item_id}"
AIHUB_TEMPORARY_UPLOAD_REDIS_TTL_SECONDS = 7 * 24 * 60 * 60

# OpenWebUI's ``TASKS.MOA_RESPONSE_GENERATION`` (backend ``constants.py``), stamped into
# ``metadata["task"]`` by its ``/api/v1/tasks/moa/completions`` route when a user presses "Merge
# Responses". Unlike every other task value this one is user-initiated — see the two predicates below.
MOA_RESPONSE_GENERATION_TASK = "moa_response_generation"

# Salts the merge thread_id so it can never collide with an agent thread (those are salted with
# ``agent_class/agent_id``), while staying stable per chat so repeated merges group into one
# LiteLLM/Langfuse session.
MOA_MERGE_THREAD_SALT = "moa-merge"

# Agents cite a source by the id on its ``REFERENCE_DOCUMENT`` tag (``CitationId`` in swiss_ai_hub.core), e.g.
# ``[s3f9a1c]``. Open WebUI only links numbers, 1-based into the message's source list, so the pipe rewrites them.
CITATION_MARKER_PATTERN = re.compile(r"(\s*)\[\s*(s[0-9a-f]{6}(?:\s*[,;]\s*s[0-9a-f]{6})*)\s*\]")
CITATION_ID_PATTERN = re.compile(r"s[0-9a-f]{6}")
UNFINISHED_CITATION_PATTERN = re.compile(r"\[\s*s[0-9a-f]{0,6}(?:\s*[,;]\s*s[0-9a-f]{0,6})*$")

# A markdown link or image a model wrote, its target optionally in ``<…>`` and followed by a title. A ``[`` right after
# a word, ``]`` or ``)`` indexes code (``df[col](x)``) rather than opening a link, so it is left alone.
MARKDOWN_LINK_PATTERN = re.compile(r"(?<![\w\])])(!?)\[([^\]\n]*)\]\(\s*<?([^\s<>()]+)>?(?:\s+\"[^\"\n]*\")?\s*\)")
URL_SCHEME_PATTERN = re.compile(r"^([a-z][a-z0-9+.-]*):", re.IGNORECASE)
FILE_EXTENSION_PATTERN = re.compile(r"\.[A-Za-z0-9]{1,8}$")
# OpenAI's code interpreter links its files as ``sandbox:/mnt/data/<name>``, a habit models carry into our sandbox.
SANDBOX_LINK_SCHEMES = ("sandbox", "file")


# ============================================================================
# Domain Models with Inheritance
# ============================================================================


class BlockType(StrEnum):
    TEXT = "text"
    THINKING = "thinking"
    TOOL = "tool"
    TABLE = "table"


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
        if not self.closed:
            return f'\n<details type="reasoning" done="false">\n{self.content.strip()}</details>\n'
        # A sub-second thought has a duration of 0. Keep it done="true" — gating done on a truthy
        # duration made fast thoughts render as an unfinished "Thought" — and just drop the attribute,
        # since OpenWebUI omits the "for N seconds" suffix when there is nothing to report.
        duration_attribute = f' duration="{self.duration}"' if self.duration else ""
        return (
            f'\n<details type="reasoning" done="true"{duration_attribute}>\n'
            f"{self.content.strip()}\n"
            f"</details>\n"
        )

    def is_complete(self) -> Annotated[bool, "Whether block has content"]:
        """Thinking blocks are complete when they have content"""
        return bool(self.content)


class ToolBlock(ContentBlock):
    """Block representing tool/function execution"""

    type: Annotated[BlockType, "Block type"] = Field(default=BlockType.TOOL, frozen=True)
    tool_id: Annotated[str, "Unique identifier for the tool call"]
    tool_name: Annotated[str, "Name of the tool being called"]
    tool_params: Annotated[dict[str, Any], "Parameters passed to the tool"] = Field(default_factory=dict)
    result: Annotated[Optional[str], "What the tool returned, once it has"] = None
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
        done_status = "true" if self.closed or self.result is not None else "false"
        # Open WebUI shows the result inside the tool's collapsible, in the attribute its own tools use.
        result_attribute = f' result="{html.escape(json.dumps(self.result, ensure_ascii=False))}"' if self.result is not None else ""

        status_text = "Tool Executed" if done_status == "true" else f"Calling {self.tool_name}..."

        return (
            f'\n<details type="tool_calls" done="{done_status}" id="{html.escape(self.tool_id)}" '
            f'name="{html.escape(self.tool_name)}" arguments="{escaped_params}"{result_attribute}>\n'
            f"<summary>{status_text}</summary>\n"
            f"</details>\n"
        )

    def is_complete(self) -> Annotated[bool, "Always true for tool blocks"]:
        """Tool blocks are always complete once created"""
        return True


class TableBlock(ContentBlock):
    """A table an agent extracted while the model works on in its tool loop.

    It stays where it arrived, between the tool calls and the answer, and is never folded into a thought: the model
    only reads the table's summary and refers to it, so the table itself must reach the user as delivered.
    """

    type: Annotated[BlockType, "Block type"] = Field(default=BlockType.TABLE, frozen=True)
    content: Annotated[str, "The table and its summary, as markdown"]

    def to_html(self) -> Annotated[str, "The table as markdown"]:
        return f"\n\n{self.content.strip()}\n\n"

    def is_complete(self) -> Annotated[bool, "Always true for table blocks"]:
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

    # ``StreamingStateManager.serialize_to_html`` concatenates blocks flat, never nested, and both
    # ThinkingBlock and ToolBlock always emit a closing tag, so a non-greedy match is sufficient.
    # ``[^>]*`` is safe on the tool block because its ``arguments`` attribute is html-escaped.
    # Only the generated block types match, so a ``<details>`` an answer itself contains keeps its content.
    _DETAILS_BLOCK = re.compile(
        r'\n?<details\b[^>]*\btype="(?:reasoning|tool_calls|code_interpreter)"[^>]*>.*?</details>\n?', re.DOTALL
    )
    # Fallback for the pathological case of a model writing a literal ``</details>`` inside its own
    # reasoning text, which closes the match above early and leaves a stray tag behind.
    _ORPHAN_MARKUP = re.compile(r"</?(?:details|summary)\b[^>]*>")
    # ``AgentFileAttachmentService.download_links`` ends an answer with links to the files it attached. A model
    # handed that line copies it for the file it just made, keeping the earlier file's url, so its link downloads
    # the earlier file. The whole line goes, with any copy a model already wrote, and any other link to a file
    # loses its url.
    _DOWNLOAD_LINE = re.compile(
        r"\n*^Download: [^\n]*\]\([^)\s]*/api/v1/files/[^)\s/]+/content\)[^\n]*$", re.MULTILINE
    )
    _FILE_LINK = re.compile(r"!?\[([^\]\n]*)\]\([^)\s]*/api/v1/files/[^)\s/]+/content\)")
    # An extracted table an agent answered with, marked by core's ``ExtractedTableMarkup``. Every later message would
    # carry it back to the agent, hundreds of rows on every event of the conversation, so it goes down to one line;
    # the summary after it stays.
    _EXTRACTED_TABLE = re.compile(
        r'^\[aihub-extracted-table\]: # "rows=(\d+)"[ \t]*\r?$.*?^\[/aihub-extracted-table\]: #[ \t]*(?=\r?$)',
        re.DOTALL | re.MULTILINE,
    )
    # A removed block leaves the newlines that surrounded it; collapse the run so the text either side
    # does not end up glued into one line (nor separated by a growing gap).
    _EXCESS_BLANK_LINES = re.compile(r"\n{3,}")

    @classmethod
    def strip_agent_markup(
        cls, text: Annotated[str, "Agent answer or rendered MoA prompt"]
    ) -> Annotated[str, "Plain text"]:
        """Remove the reasoning/tool ``<details>`` blocks and the file downloads this pipeline adds to its answers.

        An earlier answer and a merged response both reach a model as raw message content, carrying this
        pipeline's own markup. A model handed it wastes context on it and imitates it: a merge model echoes the
        markup into its prose, an agent writes a tool block as text instead of calling the tool, making up
        the result, and it links a new file to an earlier file's download.
        """
        stripped = cls._EXTRACTED_TABLE.sub(r"[A table of \1 extracted rows was shown here.]", text)
        stripped = cls._DETAILS_BLOCK.sub("\n", stripped)
        stripped = cls._ORPHAN_MARKUP.sub("", stripped)
        stripped = cls._DOWNLOAD_LINE.sub("", stripped)
        stripped = cls._FILE_LINK.sub(r"\1", stripped)
        return cls._EXCESS_BLANK_LINES.sub("\n\n", stripped)

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
        if msg.get("role") == "assistant":
            blocks = [
                {**block, "text": self.strip_agent_markup(block["text"])}
                if block.get("block_type") == "text"
                else block
                for block in blocks
            ]

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


class CitationRegistry:
    """The message's source list as Open WebUI numbers it, and the rewrite of cited ids into those numbers.

    Open WebUI resolves ``[n]`` to the n-th distinct source of the message, counted in the order sources arrived and
    keyed the way ``getSourceIds`` keys them (``ContentRenderer.svelte``). Every source goes through here, memories
    included, so the numbers stay aligned even for sources no agent cites. An id the pipe never emitted as a source
    is dropped rather than shown as a dead marker. Two documents sharing a label, such as an attached
    ``contract.pdf`` and a knowledge document of the same name, would share a number, so the later one is renamed
    ``contract.pdf (2)``.
    """

    def __init__(self) -> None:
        self._keys: list[str] = []
        self._numbers: dict[str, int] = {}
        self._label_owners: dict[str, str] = {}
        self._labels_by_document: dict[str, str] = {}

    @staticmethod
    def key_of(source_data: Annotated[dict[str, Any], "Open WebUI source payload"]) -> Annotated[str, "Dedupe key"]:
        metadata = (source_data.get("metadata") or [{}])[0]
        source_id = metadata.get("source") or "N/A"
        if metadata.get("name"):
            return metadata["name"]
        if source_id.startswith(("http://", "https://")):
            return source_id
        return source_data.get("source", {}).get("name") or source_id

    @staticmethod
    def document_of(source_data: Annotated[dict[str, Any], "Open WebUI source payload"]) -> Annotated[str, "Identity"]:
        """What Open WebUI's source modal groups by, so it tells two same-named documents apart."""
        metadata = (source_data.get("metadata") or [{}])[0]
        return metadata.get("source") or source_data.get("source", {}).get("id") or CitationRegistry.key_of(source_data)

    def register(
        self,
        source_data: Annotated[dict[str, Any], "Open WebUI source payload"],
        citation_id: Annotated[Optional[str], "Id the agent cites this source by"] = None,
    ) -> Annotated[dict[str, Any], "The payload to emit, relabelled when its label was taken"]:
        source_data = self._with_unique_label(source_data)
        key = self.key_of(source_data)
        if key not in self._keys:
            self._keys.append(key)
        if citation_id and citation_id not in self._numbers:
            self._numbers[citation_id] = self._keys.index(key) + 1
        return source_data

    def _with_unique_label(self, source_data: dict[str, Any]) -> dict[str, Any]:
        document = self.document_of(source_data)
        label = self._labels_by_document.get(document)
        if label is None:
            label = base = self.key_of(source_data)
            suffix = 2
            while self._label_owners.get(label, document) != document:
                label = f"{base} ({suffix})"
                suffix += 1
            self._label_owners[label] = document
            self._labels_by_document[document] = label
        if label == self.key_of(source_data):
            return source_data
        return {
            **source_data,
            "source": {**source_data.get("source", {}), "name": label},
            "metadata": [{**metadata, "name": label} for metadata in source_data.get("metadata") or [{}]],
        }

    def resolve(self, content: Annotated[str, "Rendered message content"]) -> Annotated[str, "Content Open WebUI links"]:
        resolved = CITATION_MARKER_PATTERN.sub(self._numbered, content)
        return UNFINISHED_CITATION_PATTERN.sub("", resolved)

    def _numbered(self, match: re.Match) -> str:
        numbers = []
        for citation_id in CITATION_ID_PATTERN.findall(match.group(2)):
            number = self._numbers.get(citation_id)
            if number is not None and number not in numbers:
                numbers.append(number)
        if not numbers:
            return ""
        return match.group(1) + "".join(f"[{number}]" for number in numbers)


class FileLinkRegistry:
    """The files attached to the answer by name, and the rewrite of the links a model writes to them into downloads.

    Told never to, a model still links a file it made the way it knows from elsewhere: ``sandbox:<name>``, its sandbox
    path or a bare name, none of which a browser opens. Such a link is pointed at the file's download, or reduced to
    its label when the answer attached no file of that name. The raw text keeps the model's link, so one written before
    its file arrives resolves on the next render.
    """

    def __init__(self) -> None:
        self._urls: dict[str, str] = {}

    def register(self, file: Annotated[dict[str, Any], "The attached file as a message file entry"]) -> None:
        self._urls[file["name"].casefold()] = file["url"]

    def resolve(
        self, content: Annotated[str, "Rendered message content"]
    ) -> Annotated[str, "Content whose file links open"]:
        return MARKDOWN_LINK_PATTERN.sub(self._linked, content)

    def _linked(self, match: re.Match) -> str:
        image, label, target = match.groups()
        name = self.sandbox_file_name(target)
        if name is None:
            return match.group(0)
        url = self._urls.get(name.casefold())
        return f"{image}[{label}]({url})" if url else label

    @staticmethod
    def sandbox_file_name(
        target: Annotated[str, "A link's target"],
    ) -> Annotated[Optional[str], "The name of the sandbox file it points at, or None for a link a browser opens"]:
        path = target.split("#", 1)[0].split("?", 1)[0]
        scheme = URL_SCHEME_PATTERN.match(path)
        if scheme:
            if scheme.group(1).lower() not in SANDBOX_LINK_SCHEMES:
                return None
            path = path[scheme.end() :]
        elif path.startswith(("/api/", "//")) or not FILE_EXTENSION_PATTERN.search(path):
            return None
        return urllib.parse.unquote(path.rstrip("/").rsplit("/", 1)[-1]) or None


class StreamingStateManager:
    """Manages streaming content state with proper encapsulation"""

    def __init__(self):
        self.citations = CitationRegistry()
        self.files = FileLinkRegistry()
        self._content_blocks: Annotated[list[ContentBlock], "List of finalized content blocks"] = []
        self._current_block: Annotated[Optional[ContentBlock], "Currently active block being built"] = None
        self._deferred_thinking: Annotated[
            Optional[ThinkingBlock], "Thoughts that arrived while an answer was streaming"
        ] = None
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
        # A thought arriving while an answer is streaming comes from a step running concurrently with
        # it (title generation, follow-up questions), not from the answer itself — display events carry
        # no step identity, so arrival order is all we have. Opening a block here would finalize the
        # text block and cut the answer into two paragraphs with a "Thought" wedged between them, so
        # redirect it to the run's existing reasoning block and keep the answer contiguous.
        if isinstance(self._current_block, TextBlock):
            self._defer_thought(content)
            return

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
        # Text streamed right before a tool call is the model talking to itself ("let me check…"), not the answer,
        # so it moves into a collapsed thought instead of staying at the top of the reply.
        if isinstance(self._current_block, TextBlock) and self._current_block.content.strip():
            thought = self._block_factory.create_thinking_block(self._current_block.content).with_closure()
            self._current_block = thought
        # Close any open blocks
        self._close_open_blocks()
        self._finalize_current_block()
        # A tool call ends the current phase, so deferred thoughts belong before it, not after the run.
        self._flush_deferred_thoughts()

        self._current_block = self._block_factory.create_tool_block(
            tool_id=tool_id, tool_name=tool_name, tool_params=tool_params
        )

    def complete_tool_block(
        self,
        tool_id: Annotated[str, "Tool call identifier"],
        result: Annotated[str, "What the tool returned"],
    ) -> None:
        """Put a tool's result into its block, wherever the block ended up while later content streamed"""
        if isinstance(self._current_block, ToolBlock) and self._current_block.tool_id == tool_id:
            self._current_block = self._current_block.model_copy(update={"result": result}).with_closure()
            return
        for index, block in enumerate(self._content_blocks):
            if isinstance(block, ToolBlock) and block.tool_id == tool_id:
                self._content_blocks[index] = block.model_copy(update={"result": result, "closed": True})

    def add_table_block(self, content: Annotated[str, "The table and its summary, as markdown"]) -> None:
        """Pin an extracted table where the run has got to, behind the blocks so far"""
        self._close_open_blocks()
        self._finalize_current_block()
        self._content_blocks.append(TableBlock(content=content))

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
        self._flush_deferred_thoughts()

    def _defer_thought(self, content: Annotated[str, "Reasoning content to defer"]) -> None:
        """Route a thought that arrived mid-answer out of the answer's way.

        Preferred target is the reasoning block the run already opened, so one message carries one
        collapsible and the answer stays last on screen. Its recorded duration is left untouched:
        the block measures the pre-answer thinking, and stretching it across the answer this thought
        arrived during would report a wait the user never had.
        """
        merge_index = self._last_thinking_block_index()
        if merge_index is not None:
            self._content_blocks[merge_index] = self._content_blocks[merge_index].with_content(content)
            return

        # Nothing to merge into (the run streamed an answer without thinking first), so hold the
        # thought for a trailing block rather than splitting the answer to place it.
        block = self._deferred_thinking or self._block_factory.create_thinking_block()
        self._deferred_thinking = block.with_content(content).with_closure()

    def _last_thinking_block_index(self) -> Annotated[Optional[int], "Index of the newest finalized thinking block"]:
        """Locate the run's existing reasoning block, if it has one"""
        for index in reversed(range(len(self._content_blocks))):
            if isinstance(self._content_blocks[index], ThinkingBlock):
                return index
        return None

    def _flush_deferred_thoughts(self) -> None:
        """Move deferred thoughts behind the content they were held back for"""
        if not self._deferred_thinking:
            return

        self._finalize_current_block()
        self._content_blocks.append(self._deferred_thinking)
        self._deferred_thinking = None

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
        blocks = [*self._content_blocks, *([self._current_block] if self._current_block else [])]
        # Deferred thoughts render live at the tail so reasoning stays visible while it happens; the
        # answer above them keeps growing, and flushing later lands them in this same position.
        if self._deferred_thinking:
            blocks.append(self._deferred_thinking)
        # A table's cells are document text, never citations or file links, so they are shown as extracted.
        return "".join(
            block.to_html()
            if isinstance(block, (ToolBlock, TableBlock))
            else self.files.resolve(self.citations.resolve(block.to_html()))
            for block in blocks
        )


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
        chat_id: Annotated[Optional[str], "OpenWebUI chat id, for persisting title/follow-ups"] = None,
        message_id: Annotated[Optional[str], "OpenWebUI message id, for persisting follow-ups"] = None,
        redis: Annotated[Any, "OpenWebUI async redis client, for stashing the agent title"] = None,
        owui_file_ids: Annotated[Optional[dict[str, str]], "Agent file id -> Open WebUI file id"] = None,
        attachments: Annotated[Any, "Registers files the agent showed as Open WebUI files"] = None,
    ):
        self.owui_file_ids = owui_file_ids or {}
        self.attachments = attachments
        self.state_manager = state_manager
        self.emitter = emitter
        self.caller = caller
        self.headers = headers
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.thread_id = thread_id
        self.stream_service = stream_service
        self.chat_id = chat_id
        self.message_id = message_id
        self.redis = redis

    async def emit_source(
        self,
        source_data: Annotated[dict[str, Any], "Open WebUI source payload"],
        citation_id: Annotated[Optional[str], "Id the agent cites this source by"] = None,
    ) -> None:
        source_data = self.state_manager.citations.register(source_data, citation_id)
        await self.emitter({"type": "source", "data": source_data})

    async def attach_file(
        self, file: Annotated[dict[str, Any], "A file in our storage: bucket, key, filename and content_type"]
    ) -> None:
        """Attach a file the agent produced to the answer, so it downloads like an upload."""
        attached = await self.attachments.attach(file, self.chat_id, self.message_id)
        self.state_manager.files.register(attached)
        # Open WebUI's server appends a `files` event to the message while its browser replaces the list with it,
        # so the new file is persisted on its own and the browser then gets every file of the answer.
        await self.emitter({"type": "files", "data": {"files": [attached]}})
        await self.emitter({"type": "chat:message:files", "data": {"files": self.attachments.attached}})


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
        tool_name = event.get("label") or event.get("name") or "Unknown Tool"
        parameters = event.get("parameters") or {}
        tool_id = event.get("tool_call_id") or event.get("event_id", "")

        await context.emitter(
            {
                "type": "status",
                "data": {"action": None, "description": tool_name, "done": False},
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


class ToolResultEventHandler(EventHandler):
    """Shows what a tool the agent chose returned, inside that tool's collapsible block."""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if tool result event"]:
        return "ToolResultEvent" in [event.get("_event_name"), *event.get("_parent_event_names", [])]

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Tool result event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        content = event.get("content", "")
        result = f"Error: {content}" if event.get("is_error") and not content.startswith("Error") else content
        context.state_manager.complete_tool_block(event.get("tool_call_id", ""), result)
        await context.emitter({"type": "replace", "data": {"content": context.state_manager.serialize_to_html()}})
        await context.emitter({"type": "status", "data": {"action": None, "description": "", "done": True}})
        return True


class ToolLoopStatusEventHandler(EventHandler):
    """What the agent's tool loop is doing when nothing else shows it: deciding in the background, or condensing
    earlier results to fit the model's context."""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if tool loop status event"]:
        names = [event.get("_event_name"), *event.get("_parent_event_names", [])]
        return "ToolLoopStatusEvent" in names or "ToolLoopCondensedEvent" in names

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Tool loop status event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        await context.emitter(
            {
                "type": "status",
                "data": {
                    "action": None,
                    "description": event.get("description", ""),
                    "done": bool(event.get("done", event.get("_event_name") == "ToolLoopCondensedEvent")),
                },
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
    """Reports how many documents were found; the sources come from what the model is handed, see below."""

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


class GroundingNodesEventHandler(EventHandler):
    """Lists the knowledge documents the answer is grounded in as sources, one per document: a knowledge agent's own
    retrieval, and the collections the user referenced with `#`.

    The grounding nodes are exactly what the model reads, after reranking and with carried prior-turn documents, so
    every document it can cite is listed and none it never saw. Chunks of one document share the document's
    citation id and become one source holding each chunk.
    """

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if grounding nodes event"]:
        names = {event.get("_event_name"), *event.get("_parent_event_names", [])}
        return bool(names & {"InOrderNodeCombinerEvent", "KnowledgeSearchedEvent"})

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Grounding nodes event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        documents: dict[str, list[dict[str, Any]]] = {}
        for node in event.get("grounding_nodes") or []:
            documents.setdefault(node.get("citation_id") or node.get("source", ""), []).append(node)
        for citation_id, nodes in documents.items():
            await context.emit_source(self.source_data(nodes), citation_id)
        return True

    @staticmethod
    def source_data(
        nodes: Annotated[list[dict[str, Any]], "Nodes of one document"],
    ) -> Annotated[dict[str, Any], "Source data structure"]:
        first = nodes[0]
        reference_url = GroundingNodesEventHandler.document_link(first)
        source_data: dict[str, Any] = {
            "source": {
                "name": GroundingNodesEventHandler.display_name(first),
                "id": first.get("document_id", ""),
            },
            "document": [node.get("content", "") for node in nodes],
            "metadata": [GroundingNodesEventHandler._node_metadata(node, reference_url) for node in nodes],
        }
        if reference_url:
            source_data["source"]["url"] = reference_url
        if all("score" in node for node in nodes):
            source_data["distances"] = [node["score"] for node in nodes]
        return source_data

    @staticmethod
    def document_link(node: Annotated[dict[str, Any], "Node data"]) -> Annotated[str, "Link a user can open, or ''"]:
        """The document's place outside the platform: an explicit reference link, else the original source its pipeline
        recorded, such as a markdown file's frontmatter `url`. Only web links are offered, since this becomes an href.
        """
        link = (node.get("metadata") or {}).get("reference_url") or node.get("source_origin") or ""
        return link if urlparse(link).scheme in ("http", "https") else ""

    @staticmethod
    def display_name(node: Annotated[dict[str, Any], "Node data"]) -> Annotated[str, "Label on the citation chip"]:
        """The document's title or file name; its storage URL is not something a user can open."""
        source = node.get("source", "")
        return node.get("document_title") or source.rstrip("/").rsplit("/", 1)[-1] or "Unknown Source"

    @staticmethod
    def _node_metadata(
        node: Annotated[dict[str, Any], "Node data"], reference_url: Annotated[str, "Document link"]
    ) -> Annotated[dict[str, Any], "Open WebUI metadata of one chunk"]:
        metadata = {
            "source": node.get("source", ""),
            "name": GroundingNodesEventHandler.display_name(node),
            "document_title": node.get("document_title", ""),
            "namespace": node.get("namespace", ""),
            "language": node.get("language", ""),
            "document_id": node.get("document_id", ""),
            "reference_url": reference_url,
            "created_at": node.get("created_at", ""),
        }
        if node.get("index") is not None:
            metadata["page"] = node["index"]
        return metadata


class AttachedFileEventHandler(EventHandler):
    """Shows each attached file the agent read as a source on the answer, or reports one it could not read.

    The source links to the user's original upload in Open WebUI, which is why the agent's file id is mapped back
    to the Open WebUI file it was copied from.
    """

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if attached file event"]:
        return "AttachedFileEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Attached file event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        filename = event.get("filename", "")
        if event.get("status") == "failed":
            await context.emitter(
                {
                    "type": "status",
                    "data": {"description": f"{filename}: {event.get('error') or ''}", "done": True, "error": True},
                }
            )
            return True

        owui_file_id = context.owui_file_ids.get(event.get("file_id", ""))
        name = f"{filename} (partial)" if event.get("status") == "truncated" else filename
        metadata: dict[str, Any] = {"source": owui_file_id or filename, "name": name}
        if owui_file_id:
            metadata["file_id"] = owui_file_id
        await context.emit_source(
            {
                "source": {"id": owui_file_id or event.get("file_id", ""), "name": name},
                "document": [event.get("content") or ""],
                "metadata": [metadata],
            },
            event.get("citation_id"),
        )
        return True


class FetchWebPagesEventHandler(EventHandler):
    """Shows that the agent is reading the pages the user linked. Every turn asks, so a turn that links nothing
    stays silent, and so does one whose profile has web fetch off, since its links are left unread."""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if web page fetch request"]:
        return event.get("_event_name") == "FetchWebPagesEvent"

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Web page fetch request"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        if event.get("urls") and event.get("reading", True):
            description = event.get("display_description", {}).get("en", "Reading the linked web pages")
            status = {"action": None, "description": description, "done": False}
            await context.emitter({"type": "status", "data": status})
        return True


class WebPagesFetchedEventHandler(EventHandler):
    """Lists each page the agent read as a source, by its title and URL, and reports the links it could not read.

    The answer itself explains why a page was not read; the status names the links, so the user sees it even when
    the answer does not dwell on them.
    """

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if web pages fetched event"]:
        return event.get("_event_name") == "WebPagesFetchedEvent"

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Web pages fetched event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        pages = event.get("grounding_nodes") or []
        failures = event.get("failures") or []
        for page in pages:
            await context.emit_source(GroundingNodesEventHandler.source_data([page]), page.get("citation_id"))
        if pages:
            description = f"Read {len(pages)} web page" + ("s" if len(pages) != 1 else "")
            status = {"action": None, "description": description, "done": True}
            await context.emitter({"type": "status", "data": status})
        if failures:
            unread = ", ".join(failure.get("url", "") for failure in failures)
            await context.emitter(
                {"type": "status", "data": {"description": f"Could not read: {unread}", "done": True, "error": True}}
            )
        if not pages and not failures:
            await context.emitter({"type": "status", "data": {"action": None, "description": "", "done": True}})
        return True


class RecordsExtractedEventHandler(EventHandler):
    """Attaches the whole table of an extraction to the answer, and shows the preview of one a model extracted.

    The event carries only a preview; every row is in a CSV file in our storage, which becomes a file of the answer.
    A blueprint that extracts on its own streams the preview as its answer, so the preview is only shown here for a
    result answering a tool call, whose model reads just the summary. Open WebUI re-renders the whole message on every
    event, so the preview shown inline is capped by size as well; its summary always follows it. An event from before
    tables were stored as files holds its whole table and has no file: its table is shown capped the same way.
    """

    INLINE_ROWS = 100
    INLINE_CHARACTERS = 64_000

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True for an extracted table"]:
        return event.get("_event_name") == "RecordsExtractedEvent"

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Records extracted event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        if event.get("file"):
            await context.attach_file(event["file"])
        if event.get("tool_call_id") and event.get("table"):
            context.state_manager.add_table_block(f"{self._inline(event)}\n\n{event.get('summary', '')}")
            await context.emitter({"type": "replace", "data": {"content": context.state_manager.serialize_to_html()}})
        return True

    def _inline(self, event: Annotated[dict[str, Any], "Records extracted event"]) -> Annotated[str, "Table"]:
        table = event["table"]
        lines = table.split("\n")
        rows = [line for line in lines if line.startswith("|")]
        header, body = rows[:2], rows[2:]
        kept = self._within_size(header, body)
        total = max(event.get("total_row_count") or 0, len(body))
        if len(kept) == total:
            return table
        cut = "\n".join([*header, *kept])
        where = " The whole table is attached as a file." if event.get("file") else ""
        note = f"_Showing the first {len(kept)} of {total} rows here.{where}_"
        # The marker keeps the table's real row count: the condensed line later says how many rows were found.
        return f"{lines[0]}\n\n{cut}\n\n{note}\n\n[/aihub-extracted-table]: #"

    def _within_size(
        self, header: Annotated[list[str], "Header and separator rows"], body: Annotated[list[str], "Table rows"]
    ) -> Annotated[list[str], "The leading rows that fit inline"]:
        kept: list[str] = []
        size = sum(len(line) for line in header)
        for row in body[: self.INLINE_ROWS]:
            size += len(row) + 1
            if size > self.INLINE_CHARACTERS:
                break
            kept.append(row)
        return kept


class SandboxFileDisplayedEventHandler(EventHandler):
    """Attaches a file the agent showed from the user's code sandbox to the answer, as an Open WebUI file."""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if sandbox file displayed event"]:
        return event.get("_event_name") == "SandboxFileDisplayedEvent"

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Sandbox file displayed event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        await context.attach_file(event)
        return True


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
                await context.emit_source(source_data)

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

        name = f"💭 Memory: {memory_text[:100]}{'...' if len(memory_text) > 100 else ''}"
        source_data = {
            "source": {
                "name": name,
                "id": memory_id,
            },
            "document": [memory_text],
            "metadata": [
                {
                    "source": name,
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
                await context.emit_source(source_data)

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

        name = f"🏢 Org Memory: {memory_id[:8]}..."
        source_data = {
            "source": {
                "name": name,
                "id": memory_id,
            },
            "document": [memory_text],
            "metadata": [
                {
                    "source": name,
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


class ConversationTitleEventHandler(EventHandler):
    """Relay the agent-produced conversation title to OpenWebUI (sets the chat title).

    OpenWebUI's ``chat:title`` socket handler only refreshes the UI from the DB — it does not persist.
    So we write the title to the chat first (mirroring OpenWebUI's own title task), then emit the event
    to update the live view. The emit payload is the bare title string, as the frontend does
    ``chatTitle.set(data)``.

    On the first turn OpenWebUI's post-response ``background_tasks_handler`` overwrites the chat title
    with the user's prompt (its built-in fallback, which fires regardless of ``ENABLE_TITLE_GENERATION``
    and runs *after* this pipe). To win that race we also stash the title in Redis; the
    ``aihub_title_filter`` outlet — which runs after ``background_tasks_handler`` — re-applies it.
    """

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if event contains ConversationTitleEvent"]:
        return "ConversationTitleEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Conversation title event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        title = event.get("title")
        if title:
            if is_saved_chat_id(context.chat_id):
                await Chats.update_chat_title_by_id(context.chat_id, title)
                if context.redis is not None:
                    await context.redis.set(
                        AIHUB_TITLE_REDIS_KEY.format(chat_id=context.chat_id),
                        title,
                        ex=AIHUB_TITLE_REDIS_TTL_SECONDS,
                    )
            await context.emitter({"type": "chat:title", "data": title})
        return True


class FollowUpQuestionsEventHandler(EventHandler):
    """Relay the agent-produced follow-up questions to OpenWebUI (renders follow-up suggestions)."""

    async def can_handle(
        self, event: Annotated[dict[str, Any], "Event to check"]
    ) -> Annotated[bool, "True if event contains FollowUpQuestionsEvent"]:
        return "FollowUpQuestionsEvent" in event.get("_parent_event_names", [])

    async def handle(
        self,
        event: Annotated[dict[str, Any], "Follow-up questions event"],
        context: Annotated[EventContext, "Processing context"],
    ) -> Annotated[bool, "Always returns True"]:
        questions = event.get("questions") or []
        if questions:
            await context.emitter({"type": "chat:message:follow_ups", "data": {"follow_ups": questions}})
            if context.message_id and is_saved_chat_id(context.chat_id):
                await Chats.upsert_message_to_chat_by_id_and_message_id(
                    context.chat_id, context.message_id, {"followUps": questions}
                )
        return True


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
            ToolResultEventHandler(),
            ToolLoopStatusEventHandler(),
            HumanInTheLoopHandler(),
            ExceptionEventHandler(),
            EmbeddingEventHandler(),
            RetrieverEventHandler(),
            GroundingNodesEventHandler(),
            AttachedFileEventHandler(),
            FetchWebPagesEventHandler(),
            WebPagesFetchedEventHandler(),
            SandboxFileDisplayedEventHandler(),
            RecordsExtractedEventHandler(),
            RetrieveUserMemoryEventHandler(),
            RetrieveOrganizationMemoryEventHandler(),
            ConversationTitleEventHandler(),
            FollowUpQuestionsEventHandler(),
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
        url = f"{self._base_url}/api/v1/active/agents/classes/{agent_class}/instances/{agent_id}/{event_name}/stream"
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
        chat_id: Annotated[Optional[str], "OpenWebUI chat id, for persisting title/follow-ups"] = None,
        message_id: Annotated[Optional[str], "OpenWebUI message id, for persisting follow-ups"] = None,
        redis: Annotated[Any, "OpenWebUI async redis client, for stashing the agent title"] = None,
        stream_start_callback: Annotated[Callable | None, "Stream start callback"] = None,
        owui_file_ids: Annotated[Optional[dict[str, str]], "Agent file id -> Open WebUI file id"] = None,
        attachments: Annotated[Any, "Registers files the agent showed as Open WebUI files"] = None,
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
            chat_id=chat_id,
            message_id=message_id,
            redis=redis,
            owui_file_ids=owui_file_ids,
            attachments=attachments,
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
                    if attachments and (links := attachments.download_links(state_manager.serialize_to_html())):
                        state_manager.close_current_block()
                        state_manager.start_text_block(links)
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
            chat_id=context.chat_id,
            message_id=context.message_id,
            redis=context.redis,
            owui_file_ids=context.owui_file_ids,
            attachments=context.attachments,
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
        locale: Annotated[str, "Locale for resolving agent names"],
    ):
        self._base_url = base_url
        self._api_key = api_key
        self._prefix = prefix
        self._timeout = timeout
        self._locale = locale

    async def discover_agents(
        self,
    ) -> Annotated[list[dict[str, str]], "List of available agents with id and name"]:
        """Fetch available conversational agents"""
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Accept": "application/json",
                "Accept-Language": self._locale,
            }

            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(f"{self._base_url}/api/v1/active/agents/instances", headers=headers)
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


class AgentFileAttachmentService:
    """Registers files the agent produced as Open WebUI files on the answer, so they download like any upload.

    The agent copied each file into our storage, which Open WebUI's own storage shares, and the copy is read from
    there; the file is linked to the chat message the way Open WebUI links the images it generates.
    """

    def __init__(self, s3_client: Any, request: Any, user_id: str) -> None:
        self._s3_client = s3_client
        self._request = request
        self._user_id = user_id
        self.attached: list[dict[str, Any]] = []
        self._linked = 0

    async def attach(
        self,
        file: Annotated[dict[str, Any], "A file in our storage: bucket, key, filename and content_type"],
        chat_id: Annotated[Optional[str], "Open WebUI chat id"],
        message_id: Annotated[Optional[str], "Open WebUI message id"],
    ) -> Annotated[dict[str, Any], "The file as a message file entry"]:
        import io

        from fastapi import UploadFile
        from open_webui.routers.files import upload_file_handler

        content = await asyncio.to_thread(self._read, file["bucket"], file["key"])
        user = await Users.get_user_by_id(self._user_id)
        upload = UploadFile(
            file=io.BytesIO(content), filename=file["filename"], headers={"content-type": file["content_type"]}
        )
        item = await upload_file_handler(
            self._request,
            file=upload,
            metadata={"chat_id": chat_id, "message_id": message_id},
            process=False,
            user=user,
        )
        if message_id and is_saved_chat_id(chat_id):
            await Chats.insert_chat_files(chat_id=chat_id, message_id=message_id, file_ids=[item.id], user_id=user.id)
        entry = {
            "type": "file",
            "id": item.id,
            "url": self._request.app.url_path_for("get_file_content_by_id", id=item.id),
            "name": file["filename"],
            "content_type": file["content_type"],
            "size": len(content),
        }
        self.attached.append(entry)
        return entry

    def download_links(
        self, answer: Annotated[str, "The answer as rendered so far"]
    ) -> Annotated[str, "Markdown links to the files not linked in the answer yet"]:
        """Open WebUI hides an attachment's download behind the file name in its preview, so the answer links each one.

        A file the model linked itself, its link resolved to the download, is left out so the answer links it once.
        """
        new = self.attached[self._linked :]
        self._linked = len(self.attached)
        unlinked = [entry for entry in new if entry["url"] not in answer]
        if not unlinked:
            return ""
        return "\n\nDownload: " + " · ".join(f"[{entry['name']}]({entry['url']})" for entry in unlinked)

    def _read(self, bucket: str, key: str) -> bytes:
        return self._s3_client.get_object(Bucket=bucket, Key=key)["Body"].read()


class KnowledgeReferenceService:
    """Turns the knowledge entries the user referenced with `#` into references to our collections.

    Open WebUI assigns its own ids to knowledge entries, so the AI-Hub, which created them, resolves which collection
    each one stands for. An entry nobody resolves, such as one a user created in Open WebUI, is left out.
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    async def references_for_event(
        self,
        files: Annotated[Optional[list[dict[str, Any]]], "Files of the current message branch from Open WebUI"],
        headers: Annotated[dict[str, str], "Auth headers for AI-Hub API"],
    ) -> Annotated[list[dict[str, str]], "The referenced collections, as database and namespace"]:
        openwebui_ids = list(
            dict.fromkeys(file["id"] for file in files or [] if file.get("type") == KNOWLEDGE_COLLECTION_TYPE)
        )
        if not openwebui_ids:
            return []
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base_url}/api/v1/active/knowledge/openwebui-references",
                json={"openwebui_ids": openwebui_ids},
                headers=headers,
            )
            response.raise_for_status()
            return response.json()


class WebReferenceService:
    """Turns the web pages the user referenced with `#` into links the agent reads itself.

    Open WebUI fetches such a page in the browser as soon as it is picked and sends its text along. The agent reads
    the page through the platform's own browser instead, so the fetch is traced and checked, and only the URL is
    forwarded: Open WebUI's copy of the text is dropped.
    """

    @staticmethod
    def references_for_event(
        files: Annotated[Optional[list[dict[str, Any]]], "Files of the current message branch from Open WebUI"],
    ) -> Annotated[list[str], "The URLs of the referenced pages, once each"]:
        return list(dict.fromkeys(file["url"] for file in files or [] if WebReferenceService.is_web_reference(file)))

    @staticmethod
    def is_web_reference(file: Annotated[dict[str, Any], "One file of the branch"]) -> Annotated[bool, "A web page"]:
        """Attach Webpage sends `type: "text"` with the page's `url` and its text nested under `file.data`; a temporary
        chat's upload is `type: "text"` too, but carries its text at the top level and no URL."""
        return file.get("type") == "text" and file.get("content") is None and bool(file.get("url"))


class TemporaryUploadScope(BaseModel):
    """Where uploads of items without an Open WebUI file are remembered, a temporary chat's text and notes: without
    this each turn would upload them again. Redis only saves that copy, so a Redis error never costs the turn its file."""

    user_id: str
    thread_id: str
    redis: Any = None

    def _key(self, item_id: str) -> str:
        return AIHUB_TEMPORARY_UPLOAD_REDIS_KEY.format(user_id=self.user_id, thread_id=self.thread_id, item_id=item_id)

    async def recall(
        self, item_id: Annotated[str | None, "The id the browser gave the item when it was attached"]
    ) -> Annotated[str | None, "The agent file id of an earlier turn's upload of the item"]:
        if self.redis is None or not item_id:
            return None
        try:
            file_id = await self.redis.get(self._key(item_id))
        except Exception as e:
            logger.warning(f"Could not look up an earlier upload of {item_id}: {e}")
            return None
        return file_id.decode() if isinstance(file_id, bytes) else file_id

    async def remember(
        self,
        item_id: Annotated[str | None, "The id the browser gave the item when it was attached"],
        file_id: Annotated[str, "The agent file id the item was uploaded as"],
    ) -> None:
        if self.redis is None or not item_id:
            return
        await self.redis.set(self._key(item_id), file_id, ex=AIHUB_TEMPORARY_UPLOAD_REDIS_TTL_SECONDS)


class AgentAttachment(BaseModel):
    """One file of the turn on its way into the agent's bucket, with the upload it has there once known.

    An item Open WebUI keeps no file for, a temporary chat's text or a note, carries its `text` instead, and its upload
    is remembered in Redis under `upload_key`."""

    source: dict[str, Any]
    filename: str
    content_type: str
    file_id: str | None = None
    owui_file: Any = None
    text: str | None = None
    upload_key: str | None = None

    @property
    def owui_file_id(self) -> str | None:
        """The Open WebUI file the agent's copy came from, which the answer's citations link to."""
        if self.source.get("type", "file") == "file" and self.source.get("id"):
            return self.source["id"]
        return None

    def reference(self) -> dict[str, str]:
        return {"filename": self.filename, "file_type": self.content_type, "file_id": self.file_id}


class FileProcessingService:
    """Handles file processing via the agent file upload API.

    Uploads files from OpenWebUI's S3 storage into the agent's dedicated
    bucket using the two-step initiate/validate flow, preventing IDOR.
    """

    def __init__(self, base_url: str, s3_endpoint: str, s3_access_key: str, s3_secret_key: str) -> None:
        self._base_url = base_url
        self._owui_s3_client = self._create_s3_client(s3_endpoint, s3_access_key, s3_secret_key)

    @property
    def s3_client(self) -> Any:
        return self._owui_s3_client

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
        files: Annotated[list[dict[str, Any]] | None, "Files of the current message branch from Open WebUI"],
        agent_class: Annotated[str, "Target agent class"],
        agent_id: Annotated[str, "Target agent instance ID"],
        headers: Annotated[dict[str, str], "Auth headers for AI-Hub API"],
        thread_id: Annotated[str, "The conversation, whose folder in the user's files gets each file"],
        user_id: Annotated[str, "The Open WebUI user, whose temporary chats' uploads are remembered apart"],
        redis: Annotated[Any, "OpenWebUI async redis client, remembering a temporary chat's uploads"] = None,
    ) -> Annotated[
        tuple[list[dict[str, str]], dict[str, str]],
        "Prepared files for AI-Hub, and each agent file id mapped to the Open WebUI file id it came from",
    ]:
        """Hand every file of the branch to the agent's bucket, reusing an upload the bucket still holds.

        One validate call checks the known uploads; only what the bucket lacks is uploaded, followed by one more call
        over all the turn's files. The API places them in the user's files on the call that finds none missing, so
        the files of a turn are placed together, once.
        """
        agent_key = f"{agent_class}/{agent_id}"
        scope = TemporaryUploadScope(user_id=user_id, thread_id=thread_id, redis=redis)
        attachments = await self._resolve_all(files, agent_key, scope)
        known = [attachment for attachment in attachments if attachment.file_id]
        # With a new file in the turn the check after its upload places them all, so this one must place nothing.
        placing_thread_id = thread_id if len(known) == len(attachments) else None
        missing = await self._missing(known, agent_class, agent_id, headers, placing_thread_id)
        confirmed = {attachment.file_id for attachment in known} - missing if missing is not None else set()
        pending = [attachment for attachment in attachments if attachment.file_id not in confirmed]
        if pending:
            await self._upload_all(pending, agent_class, agent_id, headers)
            confirmed = await self._confirm(attachments, confirmed, agent_class, agent_id, headers, thread_id)
            for attachment in pending:
                if attachment.file_id in confirmed:
                    await self._remember(attachment, agent_key, scope)

        prepared = [attachment for attachment in attachments if attachment.file_id in confirmed]
        owui_file_ids = {item.file_id: item.owui_file_id for item in prepared if item.owui_file_id}
        return [attachment.reference() for attachment in prepared], owui_file_ids

    async def _resolve_all(
        self,
        files: Annotated[list[dict[str, Any]] | None, "Files of the current message branch"],
        agent_key: Annotated[str, "Agent class/id the uploads belong to"],
        scope: Annotated[TemporaryUploadScope, "Where a temporary chat's uploads are remembered"],
    ) -> Annotated[list[AgentAttachment], "The turn's files, each with its known upload if any"]:
        """A knowledge entry stands for one of our collections, which the agent searches itself, and a web page for a
        link it reads itself, so neither is a file."""
        attachments: list[AgentAttachment] = []
        for file in files or []:
            if file.get("type") == KNOWLEDGE_COLLECTION_TYPE or WebReferenceService.is_web_reference(file):
                continue
            try:
                attachment = await self._resolve(file, agent_key, scope)
            except Exception:
                logger.exception(f"Error processing file {file.get('name', '')}")
                continue
            if attachment:
                attachments.append(attachment)
        return attachments

    async def _resolve(
        self,
        file: Annotated[dict[str, Any], "Single file of the branch"],
        agent_key: Annotated[str, "Agent class/id the uploads belong to"],
        scope: Annotated[TemporaryUploadScope, "Where a temporary chat's uploads are remembered"],
    ) -> Annotated[AgentAttachment | None, "The file with its known upload, or None when Open WebUI lacks it"]:
        """A temporary chat's text, which only carries content, is uploaded as a plain-text file for the agent to read
        like any other attachment, and a note or an attached chat as a markdown file."""
        logger.debug(f"Processing file: {file.get('name', '')}, ID: {file.get('id', '')}")
        if file.get("type") == "text" and file.get("content") is not None:
            name = file.get("name") or "attachment"
            return AgentAttachment(
                source=file,
                filename=name if name.lower().endswith(".txt") else f"{name}.txt",
                content_type="text/plain",
                file_id=await scope.recall(file.get("id")),
                text=file["content"],
                upload_key=file.get("id"),
            )
        if file.get("type") == "note":
            return await self._resolve_note(file, scope)
        if file.get("type") == "chat":
            return await self._resolve_chat(file, scope)

        file_obj = await Files.get_file_by_id(file.get("id", ""))
        if not file_obj:
            logger.warning(f"Could not retrieve file with ID: {file.get('id', '')}")
            return None
        file_meta = file_obj.meta or {}
        return AgentAttachment(
            source=file,
            filename=file_meta.get("name", "unnamed_file"),
            content_type=file_meta.get("content_type", "application/octet-stream"),
            file_id=(file_meta.get(AGENT_UPLOADS_FILE_META_KEY) or {}).get(agent_key),
            owui_file=file_obj,
        )

    @staticmethod
    async def _resolve_note(
        file: Annotated[dict[str, Any], "A note the user attached"],
        scope: Annotated[TemporaryUploadScope, "Where the note's upload is remembered, for the user it belongs to"],
    ) -> Annotated[AgentAttachment | None, "The note as markdown, or None when it is gone or the user may not read it"]:
        """The pipe reads Open WebUI's database with its own rights, so it repeats Open WebUI's read check: only the
        note's owner or a user it was shared with gets it. The upload is remembered per version of the note, so an edit
        reaches the agent and an unchanged note is not copied again."""
        from open_webui.models.access_grants import AccessGrants
        from open_webui.models.notes import Notes

        note = await Notes.get_note_by_id(file.get("id", ""))
        if not note:
            logger.warning(f"Could not retrieve note with ID: {file.get('id', '')}")
            return None
        if note.user_id != scope.user_id and not await AccessGrants.has_access(
            user_id=scope.user_id, resource_type="note", resource_id=note.id, permission="read"
        ):
            logger.warning(f"User {scope.user_id} may not read note {note.id}")
            return None
        upload_key = f"note:{note.id}:{note.updated_at}"
        return AgentAttachment(
            source=file,
            filename=FileProcessingService._markdown_filename(note.title or "note"),
            content_type="text/markdown",
            file_id=await scope.recall(upload_key),
            text=((note.data or {}).get("content") or {}).get("md") or "",
            upload_key=upload_key,
        )

    @staticmethod
    async def _resolve_chat(
        file: Annotated[dict[str, Any], "A chat the user attached"],
        scope: Annotated[TemporaryUploadScope, "Where the chat's upload is remembered, for the user it belongs to"],
    ) -> Annotated[
        AgentAttachment | None, "The chat's transcript, or None when it is gone or the user may not read it"
    ]:
        """Agent models run without Open WebUI's file context, so the pipe turns an attached chat into its transcript
        itself, in Open WebUI's own format. It repeats Open WebUI's read check, since a chat id comes from the browser,
        and remembers the upload per version of the chat, so a chat that grew reaches the agent again."""
        chat = await Chats.get_chat_by_id(file.get("id", ""))
        if not chat:
            logger.warning(f"Could not retrieve chat with ID: {file.get('id', '')}")
            return None
        if not await FileProcessingService._may_read_chat(chat, scope.user_id):
            logger.warning(f"User {scope.user_id} may not read chat {chat.id}")
            return None
        transcript = FileProcessingService._chat_transcript(chat)
        if not transcript:
            return None
        upload_key = f"chat:{chat.id}:{chat.updated_at}"
        return AgentAttachment(
            source=file,
            filename=FileProcessingService._markdown_filename(chat.title or "chat"),
            content_type="text/markdown",
            file_id=await scope.recall(upload_key),
            text=transcript,
            upload_key=upload_key,
        )

    @staticmethod
    def _markdown_filename(title: Annotated[str, "A note's or chat's title"]) -> Annotated[str, "Its upload's name"]:
        """A title may hold a path separator, which the agent upload API refuses in a filename."""
        stem = title.replace("/", "-").replace("\\", "-")
        return f"{stem[: AGENT_UPLOAD_FILENAME_MAX_LENGTH - len('.md')]}.md"

    @staticmethod
    async def _may_read_chat(
        chat: Annotated[Any, "The attached chat"], user_id: Annotated[str, "The user attaching it"]
    ) -> Annotated[bool, "Whether Open WebUI lets the user read the chat"]:
        """The owner, a user it was shared with, or a user who may read the folder it lies in."""
        from open_webui.models.access_grants import AccessGrants
        from open_webui.models.folders import Folders
        from open_webui.utils.access_control.folders import has_folder_access

        if chat.user_id == user_id or await AccessGrants.has_access(
            user_id=user_id, resource_type="shared_chat", resource_id=chat.id, permission="read"
        ):
            return True
        folder = await Folders.get_folder_by_id(chat.folder_id) if chat.folder_id else None
        return bool(folder) and await has_folder_access(user_id, folder, "read", db=None)

    @staticmethod
    def _chat_transcript(chat: Annotated[Any, "The attached chat"]) -> Annotated[str, "Its current branch as markdown"]:
        from open_webui.utils.misc import get_content_from_message, get_message_list

        history = (chat.chat or {}).get("history") or {}
        messages_map, current_id = history.get("messages") or {}, history.get("currentId")
        if not messages_map or not current_id:
            return ""
        return "\n".join(
            f"#### {message.get('role', 'user').capitalize()}\n{get_content_from_message(message) or ''}\n"
            for message in get_message_list(messages_map, current_id)
        )

    async def _upload_all(
        self,
        pending: Annotated[list[AgentAttachment], "Files the agent's bucket does not hold yet"],
        agent_class: Annotated[str, "Target agent class"],
        agent_id: Annotated[str, "Target agent instance ID"],
        headers: Annotated[dict[str, str], "Auth headers"],
    ) -> None:
        """A file that fails to upload is left out rather than costing the turn the others."""
        for attachment in pending:
            try:
                attachment.file_id = await self._upload(attachment, agent_class, agent_id, headers)
            except Exception:
                logger.exception(f"Error uploading file {attachment.filename}")
                attachment.file_id = None

    async def _confirm(
        self,
        attachments: Annotated[list[AgentAttachment], "All the turn's files"],
        confirmed: Annotated[set[str], "Agent file ids the bucket was found to hold before the uploads"],
        agent_class: Annotated[str, "Target agent class"],
        agent_id: Annotated[str, "Target agent instance ID"],
        headers: Annotated[dict[str, str], "Auth headers"],
        thread_id: Annotated[str, "The conversation the files are attached in"],
    ) -> Annotated[set[str], "Agent file ids the bucket holds after the uploads"]:
        """All the turn's files are validated together once more, so they are placed together; when that check
        fails, only the files found before the uploads are known to be there."""
        stored = [attachment for attachment in attachments if attachment.file_id]
        if not stored:
            return confirmed
        missing = await self._missing(stored, agent_class, agent_id, headers, thread_id)
        if missing is None:
            return confirmed
        if missing:
            logger.warning(f"Files missing from the agent's bucket right after upload: {sorted(missing)}")
        return {attachment.file_id for attachment in stored} - missing

    async def _remember(
        self,
        attachment: Annotated[AgentAttachment, "A file just uploaded and confirmed in the agent's bucket"],
        agent_key: Annotated[str, "Agent class/id the upload belongs to"],
        scope: Annotated[TemporaryUploadScope, "Where a temporary chat's uploads are remembered"],
    ) -> None:
        """Remembered so a later turn validates the upload instead of copying the file again; forgetting only costs
        that copy, so it never fails the turn."""
        try:
            if attachment.owui_file is not None:
                known_uploads = (attachment.owui_file.meta or {}).get(AGENT_UPLOADS_FILE_META_KEY) or {}
                await Files.update_file_metadata_by_id(
                    attachment.source.get("id", ""),
                    {AGENT_UPLOADS_FILE_META_KEY: {**known_uploads, agent_key: attachment.file_id}},
                )
            elif attachment.file_id:
                await scope.remember(attachment.upload_key, attachment.file_id)
        except Exception as e:
            logger.warning(f"Could not remember the upload of {attachment.filename}: {e}")

    def _files_url(self, agent_class: str, agent_id: str, action: str) -> str:
        return f"{self._base_url}/api/v1/active/agents/classes/{agent_class}/instances/{agent_id}/files/upload/{action}"

    async def _missing(
        self,
        attachments: Annotated[list[AgentAttachment], "Files with an upload in the agent's bucket"],
        agent_class: Annotated[str, "Target agent class"],
        agent_id: Annotated[str, "Target agent instance ID"],
        headers: Annotated[dict[str, str], "Auth headers"],
        thread_id: Annotated[str | None, "The conversation to place the files in once none is missing"],
    ) -> Annotated[set[str] | None, "Agent file ids the bucket lacks, or None when the check failed"]:
        """Uploads expire after 7 days, so a known one can be gone. A failed check confirms nothing, like a missing
        file, so the files are uploaded again rather than the turn failing."""
        if not attachments:
            return set()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self._files_url(agent_class, agent_id, "validate"),
                    headers=headers,
                    json={
                        "thread_id": thread_id,
                        "files": [{"file_id": item.file_id, "filename": item.filename} for item in attachments],
                    },
                )
            response.raise_for_status()
            return set(response.json()["missing"])
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as e:
            logger.warning(f"Could not validate {len(attachments)} file(s) in the agent's bucket: {e}")
            return None

    async def _upload(
        self,
        attachment: Annotated[AgentAttachment, "File to copy into the agent's bucket"],
        agent_class: Annotated[str, "Target agent class"],
        agent_id: Annotated[str, "Target agent instance ID"],
        headers: Annotated[dict[str, str], "Auth headers"],
    ) -> Annotated[str, "The agent file id of the upload"]:
        if attachment.text is not None:
            content = attachment.text.encode()
        else:
            content = await asyncio.to_thread(self._read_file_content, attachment.owui_file)
        async with httpx.AsyncClient(timeout=30.0) as client:
            initiate_resp = await client.post(
                self._files_url(agent_class, agent_id, "initiate"),
                headers=headers,
                json={"filename": attachment.filename, "content_type": attachment.content_type},
            )
            initiate_resp.raise_for_status()
            initiate_data = initiate_resp.json()

            put_resp = await client.put(
                initiate_data["upload_url"], content=content, headers={"Content-Type": attachment.content_type}
            )
            put_resp.raise_for_status()

        logger.debug(f"Uploaded file: {attachment.filename} -> file_id={initiate_data['file_id']}")
        return initiate_data["file_id"]

    def _read_file_content(self, file_obj: Any) -> bytes:
        """Read file content from OpenWebUI's S3 storage."""
        parsed = urlparse(file_obj.path)
        if parsed.scheme != "s3":
            raise ValueError(f"Unsupported storage path scheme: {file_obj.path}")

        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        response = self._owui_s3_client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()


class ResponseMergeService:
    """Answers OpenWebUI's "Merge Responses" button with a plain LLM instead of the agent.

    The MoA prompt is a meta-instruction over answers that already exist ("synthesize these responses"),
    so handing it to the agent would run retrieval over the meta-prompt, cite sources that answer
    nothing, spend the agent's usage quota, and — because this pipeline relays the agent's title and
    follow-up protocol events into the chat — let a merge overwrite the conversation's real title and
    follow-up questions.
    """

    def __init__(
        self,
        base_url: Annotated[str, "AI-Hub API base URL"],
        model_name: Annotated[str, "Raw LiteLLM model that synthesizes the merge"],
        auth_service: Annotated["AuthenticationService", "Signs the OpenWebUI user headers"],
        timeout: Annotated[int, "Timeout for the non-streaming path"],
    ):
        self._base_url = base_url
        self._model_name = model_name
        self._auth_service = auth_service
        self._timeout = timeout

    async def merge(
        self,
        body: Annotated[dict[str, Any], "Request body"],
        user: Annotated[dict[str, str], "User information"],
        metadata: Annotated[dict[str, str], "Request metadata"],
        request: Annotated[Any, "HTTP request object"],
    ) -> Annotated[dict[str, Any] | AsyncGenerator[str, None], "Completion or SSE stream"]:
        """The frontend always asks for a stream, but the tasks route honours ``stream: false`` too."""
        if body.get("stream", False):
            return self._merge_stream(body, user, metadata, request)
        return await self._merge_blocking(body, user, metadata, request)

    async def _merge_stream(
        self,
        body: Annotated[dict[str, Any], "Request body"],
        user: Annotated[dict[str, str], "User information"],
        metadata: Annotated[dict[str, str], "Request metadata"],
        request: Annotated[Any, "HTTP request object"],
    ) -> AsyncGenerator[str, None]:
        """Forward the merge to the model gateway, yielding OpenAI-format SSE lines."""
        if not self._model_name:
            yield self._notice("Merging responses is not configured. Ask an administrator to set AIHUB_MERGE_MODEL.")
            return

        # Inside the try: a failure while building the request must still reach the user as text, or the
        # merged message stays empty — the exact symptom this path exists to remove.
        client = httpx.AsyncClient(timeout=None, follow_redirects=True)
        try:
            headers, payload = self._build_request(body, user, metadata, request)
            async with client.stream(
                "POST",
                url=f"{self._base_url}/api/v1/active/openai/chat/completions",
                json=payload,
                headers=headers,
            ) as stream_response:
                if stream_response.status_code != 200:
                    body_bytes = await stream_response.aread()
                    yield self._notice(f"Merging responses failed: {self._error_message(body_bytes)}")
                    return

                async for line in stream_response.aiter_lines():
                    line = line.strip()
                    if line:
                        yield f"{line}\n\n"
        except Exception as merge_error:
            logger.exception(f"Error while merging responses: {merge_error}")
            yield self._notice(f"Merging responses failed: {merge_error}")
        finally:
            await client.aclose()

    async def _merge_blocking(
        self,
        body: Annotated[dict[str, Any], "Request body"],
        user: Annotated[dict[str, str], "User information"],
        metadata: Annotated[dict[str, str], "Request metadata"],
        request: Annotated[Any, "HTTP request object"],
    ) -> Annotated[dict[str, Any], "OpenAI chat completion object"]:
        """Non-streaming callers are API clients, so they get the conventional ``error`` channel."""
        if not self._model_name:
            return {"error": {"message": "AIHUB_MERGE_MODEL is not configured."}}

        try:
            headers, payload = self._build_request(body, user, metadata, request)
            payload["stream"] = False
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.post(
                    url=f"{self._base_url}/api/v1/active/openai/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if response.status_code != 200:
                    return {"error": {"message": self._error_message(response.content)}}
                return response.json()
        except Exception as merge_error:
            logger.exception(f"Error while merging responses: {merge_error}")
            return {"error": {"message": str(merge_error)}}

    def _build_request(
        self,
        body: Annotated[dict[str, Any], "Request body"],
        user: Annotated[dict[str, str], "User information"],
        metadata: Annotated[dict[str, str], "Request metadata"],
        request: Annotated[Any, "HTTP request object"],
    ) -> Annotated[tuple[dict[str, str], dict[str, Any]], "Headers and payload"]:
        """Build the payload field by field rather than splatting ``body``.

        OpenWebUI has already merged the *agent* workspace model's params into the body, so splatting it
        would let an agent's ``max_tokens`` silently truncate the merge.
        """
        accept_language = request.headers.get("Accept-Language") if request else None
        headers = self._auth_service.prepare_headers(user["name"], user["email"], accept_language)
        inject(headers)

        payload = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": MessageConverter.strip_agent_markup(self._prompt_of(body))}],
            "stream": True,
            "metadata": {
                "thread_id": self._str_to_object_id(metadata.get("chat_id"), salt=MOA_MERGE_THREAD_SALT),
                "display_id": self._str_to_object_id(metadata.get("message_id")),
            },
        }
        return headers, payload

    @staticmethod
    def _prompt_of(body: Annotated[dict[str, Any], "Request body"]) -> Annotated[str, "Rendered MoA prompt"]:
        """The tasks route renders the whole MoA template into a single user message.

        Content is a plain string there, but the OpenAI schema also allows a list of parts, so join the
        text parts rather than handing a list to the regexes.
        """
        messages = body.get("messages") or []
        if not messages:
            return ""

        content = messages[-1].get("content", "")
        if isinstance(content, str):
            return content
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))

    @staticmethod
    def _str_to_object_id(
        context_id: Annotated[Optional[str], "Context ID to convert"],
        salt: Annotated[str, "Salt mixed into the hash"] = "",
    ) -> Annotated[str, "ObjectId string"]:
        if not context_id:
            return secrets.token_hex(12)
        hashed = hashlib.md5(f"{salt}:{context_id}".encode()).digest()[:12]
        return hashed.hex()

    @staticmethod
    def _error_message(body_bytes: Annotated[bytes, "Error response body"]) -> Annotated[str, "Human-readable cause"]:
        """``ModelGatewayErrorHandler`` fills ``error.message``; a bare HTTPException only ``detail``."""
        try:
            payload = json.loads(body_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return body_bytes.decode(errors="replace")[:500] or "the model gateway returned an empty error"

        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict) and error.get("message"):
                return str(error["message"])
            if payload.get("detail"):
                return str(payload["detail"])
        return json.dumps(payload)[:500]

    def _notice(self, message: Annotated[str, "Text to show in the merged bubble"]) -> Annotated[str, "SSE line"]:
        """Deliver failures as message content, never as an SSE ``error``.

        ``openAIStreamToIterator`` turns a top-level ``error`` into ``{done: true, value: ''}`` and
        ``mergeResponses`` breaks out without writing it anywhere — which is precisely the empty
        "Merged Response" skeleton this fix exists to remove. For the same reason the chunk must not
        carry ``sources``, ``selected_model_id`` or ``usage``: the iterator intercepts those before it
        reads the delta.
        """
        chunk = {
            "id": secrets.token_hex(12),
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": self._model_name or "unknown",
            "choices": [{"index": 0, "delta": {"content": f"\n> [!WARNING]\n> {message}\n"}, "finish_reason": None}],
        }
        return f"data: {json.dumps(chunk)}\n\n"


# ============================================================================
# Main Pipeline Facade
# ============================================================================


def is_response_merge_request(metadata: dict[str, Any]) -> bool:
    """True for OpenWebUI's "Merge Responses" button — the one ``task`` a user presses and waits on.

    Answered by a plain LLM rather than the agent, see ``ResponseMergeService``.
    """
    return metadata.get("task") == MOA_RESPONSE_GENERATION_TASK


def is_auxiliary_task_request(metadata: dict[str, Any]) -> bool:
    """True when OpenWebUI is calling the pipeline as its "task model", not for a real chat turn.

    OpenWebUI sets ``metadata["task"]`` for its internal auxiliary generations (title, tags, follow-up,
    query enhancement, autocomplete, …). The agent pipeline must not run the full RAG agent for these —
    their output would otherwise leak into the chat answer. The agent already emits the title and
    follow-up questions as protocol events on the real chat turn (relayed to OpenWebUI by the handlers
    above), and tags are set deterministically here, so there is nothing for a task model to produce.

    Every task is auxiliary except the response merge, which a user triggers deliberately. Defining this
    as the complement of ``is_response_merge_request`` keeps the two predicates disjoint by construction,
    so any task OpenWebUI adds in future stays blocked by default.
    """
    return bool(metadata.get("task")) and not is_response_merge_request(metadata)


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
        OPENWEBUI_MODEL_NAME_LOCALE: str = Field(
            default=os.getenv("OPENWEBUI_MODEL_NAME_LOCALE") or "en",
            description="Locale used to resolve agent names, kept in sync with the "
            "workspace-model name the provisioner writes under the same setting",
        )
        AIHUB_MERGE_MODEL: str = Field(
            default=os.getenv("AIHUB_MERGE_MODEL", ""),
            description="Raw LiteLLM model, as capability/name, that synthesizes OpenWebUI's "
            '"Merge Responses" output. Must be a plain model and not an agent. Empty disables '
            "merging with a visible notice rather than an endless spinner",
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

        # Referenced knowledge collections
        self._knowledge_reference_service = KnowledgeReferenceService(self.valves.AIHUB_BASE_URL)

        # Message Conversion
        self._message_converter = MessageConverter()

        # Agent Discovery
        self._agent_discovery = AgentDiscoveryService(
            self.valves.AIHUB_BASE_URL,
            self.valves.AIHUB_SUPERUSER_API_KEY,
            self.valves.AIHUB_PIPELINE_PREFIX,
            self.valves.AIHUB_REQUEST_TIMEOUT,
            self.valves.OPENWEBUI_MODEL_NAME_LOCALE,
        )

        # Streaming
        self._streaming_service = StreamingService(self.valves.AIHUB_BASE_URL, self.valves.AIHUB_REQUEST_TIMEOUT)

        # Response merging (plain LLM, never the agent)
        self._merge_service = ResponseMergeService(
            self.valves.AIHUB_BASE_URL,
            self.valves.AIHUB_MERGE_MODEL,
            self._auth_service,
            self.valves.AIHUB_REQUEST_TIMEOUT,
        )

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
        agent_identifier: Annotated[str, "Agent class/id, salts the thread_id so distinct agents in one chat get distinct threads"] = "",
    ) -> Annotated[tuple[str, str], "Thread and display IDs"]:
        """Generate thread and display IDs"""
        thread_id = self._str_to_object_id(chat_id, salt=agent_identifier)
        display_id = self._str_to_object_id(message_id)
        return thread_id, display_id

    def _str_to_object_id(
        self, context_id: Annotated[Optional[str], "Context ID to convert"], salt: Annotated[str, "Salt mixed into the hash"] = ""
    ) -> Annotated[str, "ObjectId string"]:
        """Convert string to ObjectId format"""
        if not context_id:
            return secrets.token_hex(12)
        hashed = hashlib.md5(f"{salt}:{context_id}".encode()).digest()[:12]
        return hashed.hex()

    @staticmethod
    async def _merge_agent_class_tag(
        chat_id: Annotated[str, "OpenWebUI chat ID"],
        agent_class: Annotated[str, "Agent class handling this turn"],
        owui_user: Annotated[Any, "OpenWebUI user model"],
    ) -> Annotated[list[str], "Tag IDs now persisted on the chat"]:
        """Add the agent-class tag to the chat without dropping the tags already on it.

        ``Chats.update_chat_tags_by_id`` *replaces* ``chat.meta["tags"]`` wholesale and then garbage-
        collects the tag rows that fell out of it, so passing just the agent class would wipe every
        user-added tag on each turn and drop the classes of other agents used in the same chat.
        OpenWebUI stores tags pre-normalized (lowercased, spaces to underscores), so normalize here
        too — otherwise the containment check re-appends the tag on every turn.
        """
        chat = await Chats.get_chat_by_id(chat_id)
        existing_tags = (chat.meta.get("tags") if chat else None) or []
        agent_tag = agent_class.replace(" ", "_").lower()
        merged_tags = existing_tags if agent_tag in existing_tags else [*existing_tags, agent_tag]
        await Chats.update_chat_tags_by_id(chat_id, merged_tags, owui_user)
        return merged_tags

    async def _set_ui_context(
        self,
        thread_id: Annotated[str, "Thread ID"],
        display_id: Annotated[str, "Display ID"],
        agent_class: Annotated[str, "Agent type behind this answer"],
        agent_id: Annotated[str, "Agent instance behind this answer"],
        event_emitter: Annotated[EventEmitter, "Event emitter function (one-way; do NOT use event_caller)"],
    ) -> None:
        """Post a `set-context` message to the parent window so its tracing/sources/memories side
        panel auto-syncs to the current thread/display.

        Uses ``event_emitter`` (one-way Socket.IO emit) rather than ``event_caller`` (emit + wait
        for ack). With OpenWebUI running multiple uvicorn workers behind a Redis-coordinated
        session pool, an emit-with-ack here can deadlock the SSE read loop: the ack has to round-
        trip via Redis to the worker holding the user's Socket.IO session, and that path is
        unreliable when the session-pool cleanup lock is lost ("Unable to renew session cleanup
        lock. Exiting."). One-way emit doesn't depend on the ack path.
        """
        # json.dumps rather than quoted interpolation: these values end up inside a script the
        # browser executes, and a model name is not ours to trust with that.
        code = f"""
        window.parent.postMessage({{
            type: 'set-context',
            thread_id: {json.dumps(thread_id)},
            display_id: {json.dumps(display_id)},
            agent_class: {json.dumps(agent_class)},
            agent_name: {json.dumps(agent_id)},
        }}, {json.dumps(self.valves.AIHUB_FRONTEND_URL)});
        """

        await event_emitter({"type": "execute", "data": {"code": code}})

    async def _check_open_chat_hitl(
        self,
        thread_id: Annotated[str, "Thread ID"],
        headers: Annotated[dict[str, str], "Request headers"],
    ) -> Annotated[dict[str, Any] | None, "Open chat HITL request or None"]:
        """Query API for open chat HITL in this thread."""
        try:
            async with httpx.AsyncClient(timeout=self.valves.AIHUB_REQUEST_TIMEOUT) as client:
                response = await client.get(
                    f"{self.valves.AIHUB_BASE_URL}/api/v1/active/threads/{thread_id}/open-chat-hitl",
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
    ) -> Annotated[
        str | dict[str, Any] | AsyncGenerator[str, None], "Empty for the agent stream, SSE/JSON for a merge"
    ]:
        """Main pipeline entry point"""
        # Extract agent information
        agent_class, agent_id = self._extract_agent_info(body["model"])

        # Layer 2 (defense in depth): if OpenWebUI is calling us as its task model (title/tag/follow-up/
        # query/autocomplete generation), short-circuit instead of running the full RAG agent — the agent
        # already produces title/follow-ups as protocol events on the real chat turn.
        if is_auxiliary_task_request(__metadata__):
            logger.info(f"Short-circuiting auxiliary task-model request (task={__metadata__.get('task')})")
            return ""

        # "Merge Responses" is the one task a user triggers, so it must produce an answer — but a plain
        # LLM's, not the agent's. Note __event_emitter__ is None here: OpenWebUI only builds one when
        # session_id, chat_id and message_id are all present, and the merge request carries no session_id.
        if is_response_merge_request(__metadata__):
            logger.info(f"Merging responses for {agent_class}.{agent_id} via {self.valves.AIHUB_MERGE_MODEL}")
            return await self._merge_service.merge(body, __user__, __metadata__, __request__)

        # Generate IDs (salt thread_id with the agent so distinct agents in one chat get distinct threads)
        thread_id, display_id = self._generate_ids(
            __metadata__.get("chat_id"), __metadata__.get("message_id"), agent_identifier=f"{agent_class}/{agent_id}"
        )

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
            state_manager = StreamingStateManager()
            try:
                logger.debug(f"Processing request for {agent_class}.{agent_id}")
                logger.debug(f"Thread ID: {thread_id}, Display ID: {display_id}")

                # Prepare authentication (forward Accept-Language for localized error messages)
                accept_language = __request__.headers.get("Accept-Language") if __request__ else None
                headers = self._auth_service.prepare_headers(__user__["name"], __user__["email"], accept_language)
                inject(headers)

                # Convert messages
                messages = self._message_converter.convert_to_event_format(body["messages"])

                redis = getattr(getattr(getattr(__request__, "app", None), "state", None), "redis", None)

                # Process files — upload to agent's dedicated bucket
                files, owui_file_ids = await self._file_service.prepare_files_for_event(
                    __files__, agent_class, agent_id, headers, thread_id, __user__["id"], redis
                )
                knowledge_references = await self._knowledge_reference_service.references_for_event(
                    __files__, headers
                )
                web_references = WebReferenceService.references_for_event(__files__)

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
                    event_payload = {
                        "messages": messages,
                        "requested_features": (__metadata__ or {}).get(REQUESTED_FEATURES_METADATA_KEY) or [],
                    }
                    if files:
                        event_payload["files"] = files
                        logger.debug(f"Attached {len(files)} file(s) to UserMessageEvent")
                    if knowledge_references:
                        event_payload["knowledge_references"] = knowledge_references
                    if web_references:
                        event_payload["web_references"] = web_references

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

                # Layer 1 (tags): deterministic, owned by the pipeline — not LLM-generated and not a
                # protocol event. Tag the conversation with the agent class that handled it, merged into
                # the tags already on the chat. OpenWebUI's chat:tags handler re-reads tags from the DB,
                # so persist before emitting. Best-effort: a tagging failure must never fail the chat turn.
                chat_id = __metadata__.get("chat_id")
                try:
                    tags = [agent_class]
                    if is_saved_chat_id(chat_id):
                        owui_user = await Users.get_user_by_id(__user__["id"])
                        if owui_user:
                            tags = await self._merge_agent_class_tag(chat_id, agent_class, owui_user)
                    await __event_emitter__({"type": "chat:tags", "data": tags})
                except Exception as tag_error:
                    logger.warning(f"Failed to set conversation tags: {tag_error}")

                async def stream_start_callback():
                    await self._set_ui_context(
                        thread_id, hitl_display_id, agent_class, agent_id, __event_emitter__
                    )

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
                    chat_id=chat_id,
                    message_id=__metadata__.get("message_id"),
                    redis=redis,
                    stream_start_callback=stream_start_callback,
                    owui_file_ids=owui_file_ids,
                    attachments=AgentFileAttachmentService(
                        self._file_service.s3_client, __request__, __user__["id"]
                    ),
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
                return state_manager.serialize_to_html()

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
                partial = state_manager.serialize_to_html()
                return f"{partial}\n\n> Error: {e}" if partial else f"Error: {e}"
