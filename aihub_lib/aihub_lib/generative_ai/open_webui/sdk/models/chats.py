from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BaseMessage(BaseModel):
    """Base class for all chat message types with common fields for tree structure"""

    id: Annotated[str | None, Field(description="Unique message identifier")] = None
    parentId: Annotated[str | None, Field(description="Parent message identifier")] = None
    childrenIds: Annotated[list[str], Field(description="Child message identifiers")] = []
    role: Annotated[str, Field(description="Role of the message sender")]
    content: Annotated[str, Field(description="Text content of the message")]
    timestamp: Annotated[int | None, Field(description="Message timestamp")] = None

    # Allow additional fields that might be present
    model_config = ConfigDict(extra="allow")


class UserMessage(BaseMessage):
    """Message from the user with model preferences"""

    role: Annotated[Literal["user"], Field(description="User role identifier")] = "user"
    models: Annotated[list[str] | None, Field(description="Preferred models to use")] = None


class AssistantMessage(BaseMessage):
    """Message from the assistant with additional metadata"""

    role: Annotated[Literal["assistant"], Field(description="Assistant role identifier")] = "assistant"
    model: Annotated[str | None, Field(description="Model identifier used for generation")] = None
    modelName: Annotated[str | None, Field(description="Human-readable model name")] = None
    modelIdx: Annotated[int | None, Field(description="Model index in the models array")] = None
    userContext: Annotated[Any | None, Field(description="User context information")] = None
    lastSentence: Annotated[str | None, Field(description="Last sentence of the response")] = None
    done: Annotated[bool | None, Field(description="Whether generation is complete")] = None
    tool_calls: Annotated[list[dict[str, Any]] | None, Field(description="Tool calls made by the assistant")] = None


class SystemMessage(BaseMessage):
    """System message providing context or instructions"""

    role: Annotated[Literal["system"], Field(description="System role identifier")] = "system"


class ToolMessage(BaseMessage):
    """Message from a tool with results of a function call"""

    role: Annotated[Literal["tool"], Field(description="Tool role identifier")] = "tool"
    tool_call_id: Annotated[str, Field(description="ID of the related tool call")]


# Type alias for any message type
ChatMessageType = UserMessage | AssistantMessage | SystemMessage | ToolMessage | dict[str, Any]


class ChatMessageContent(BaseModel):
    """
    Representation of a message within the chat history dictionary.
    Contains all fields from any message type.
    """

    id: Annotated[str | None, Field(description="Message identifier")] = None
    parentId: Annotated[str | None, Field(description="Parent message identifier")] = None
    childrenIds: Annotated[list[str], Field(description="Child message identifiers")] = []
    role: Annotated[str, Field(description="Role of the message sender")]
    content: Annotated[str, Field(description="Text content of the message")]
    timestamp: Annotated[int | None, Field(description="Message timestamp")] = None

    # User message specific fields
    models: Annotated[list[str] | None, Field(description="Models to use for generation")] = None

    # Assistant message specific fields
    model: Annotated[str | None, Field(description="Model used for generation")] = None
    modelName: Annotated[str | None, Field(description="Human-readable model name")] = None
    modelIdx: Annotated[int | None, Field(description="Model index in the models array")] = None
    userContext: Annotated[Any | None, Field(description="User context information")] = None
    lastSentence: Annotated[str | None, Field(description="Last sentence in the response")] = None
    done: Annotated[bool | None, Field(description="Whether generation is complete")] = None

    # Tool message specific fields
    tool_call_id: Annotated[str | None, Field(description="Tool call identifier")] = None
    tool_calls: Annotated[list[dict[str, Any]] | None, Field(description="Tool calls made by the assistant")] = None

    # Additional fields
    model_config = ConfigDict(extra="allow")


class ChatHistory(BaseModel):
    """Chat history containing messages and current message ID."""

    messages: Annotated[dict[str, ChatMessageContent], Field(description="Map of message IDs to message contents")]
    currentId: Annotated[str, Field(description="ID of the current/latest message")]


class ChatData(BaseModel):
    """
    Complete chat data structure as used in API requests/responses.
    """

    id: Annotated[str | None, Field(default="", description="Chat identifier")] = ""
    title: Annotated[str, Field(description="Title of the chat")]
    models: Annotated[list[str], Field(description="Models available for this chat")] = []
    params: Annotated[dict[str, Any], Field(description="Additional parameters")] = {}
    history: Annotated[ChatHistory | None, Field(description="Chat message history map")] = None
    messages: Annotated[list[ChatMessageContent] | None, Field(description="Messages in array format")] = None
    tags: Annotated[list[str], Field(description="Tags associated with this chat")] = []
    timestamp: Annotated[int | None, Field(description="Chat timestamp")] = None
    files: Annotated[list[dict[str, Any]], Field(description="Files attached to the chat")] = []

    # Allow additional fields for flexibility
    model_config = ConfigDict(extra="allow")


class ChatForm(BaseModel):
    """Form data for creating a new chat."""

    chat: Annotated[ChatData, Field(description="Complete chat data structure")]


class ChatImportForm(BaseModel):
    """Form data for importing an existing chat with additional metadata."""

    chat: Annotated[ChatData, Field(description="Complete chat data structure")]
    meta: Annotated[dict[str, Any] | None, Field(description="Additional metadata")] = None
    pinned: Annotated[bool | None, Field(default=False, description="Whether this chat should be pinned")] = False
    folder_id: Annotated[str | None, Field(description="ID of the folder to place this chat in")] = None


class ChatTitleIdResponse(BaseModel):
    """
    Simplified chat information with just ID and title.
    Used for list views.
    """

    id: Annotated[str, Field(description="Chat identifier")]
    title: Annotated[str, Field(description="Chat title")]
    updated_at: Annotated[int, Field(description="Last update timestamp")]
    created_at: Annotated[int, Field(description="Creation timestamp")]


class ChatResponse(BaseModel):
    """Complete chat response including all metadata."""

    id: Annotated[str, Field(description="Chat identifier")]
    user_id: Annotated[str, Field(description="Owner user ID")]
    title: Annotated[str, Field(description="Chat title")]
    chat: Annotated[ChatData, Field(description="Complete chat data")]
    updated_at: Annotated[int, Field(description="Last update timestamp")]
    created_at: Annotated[int, Field(description="Creation timestamp")]
    share_id: Annotated[str | None, Field(description="Share identifier")] = None
    archived: Annotated[bool, Field(description="Whether chat is archived")]
    pinned: Annotated[bool | None, Field(default=False, description="Whether chat is pinned")] = False
    meta: Annotated[dict[str, Any], Field(description="Additional metadata")] = {}
    folder_id: Annotated[str | None, Field(description="Folder identifier")] = None


class MessageForm(BaseModel):
    """Form data for updating a message."""

    content: Annotated[str, Field(description="New message content")]


class EventForm(BaseModel):
    """Form data for sending a chat message event."""

    type: Annotated[str, Field(description="Event type")]
    data: Annotated[dict[str, Any], Field(description="Event data")]


class TagForm(BaseModel):
    """Form data for chat tag operations."""

    name: Annotated[str, Field(description="Tag name")]


class TagFilterForm(TagForm):
    """Form data for filtering chats by tag with pagination."""

    skip: Annotated[int | None, Field(default=0, description="Number of results to skip")] = 0
    limit: Annotated[int | None, Field(default=50, description="Maximum number of results to return")] = 50


class CloneForm(BaseModel):
    """Form data for cloning a chat."""

    title: Annotated[str | None, Field(description="New title for the cloned chat")] = None


class ChatFolderIdForm(BaseModel):
    """Form data for updating a chat's folder."""

    folder_id: Annotated[str | None, Field(description="New folder ID")] = None


class TagModel(BaseModel):
    """Tag model for chat organization."""

    id: Annotated[str, Field(description="Tag identifier")]
    name: Annotated[str, Field(description="Tag name")]
    user_id: Annotated[str, Field(description="User identifier")]
