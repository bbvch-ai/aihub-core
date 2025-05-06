import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..client import BaseClient
from ..models.chats import (
    AssistantMessage,
    ChatData,
    ChatFolderIdForm,
    ChatForm,
    ChatHistory,
    ChatImportForm,
    ChatMessageContent,
    ChatMessageType,
    ChatResponse,
    ChatTitleIdResponse,
    CloneForm,
    EventForm,
    MessageForm,
    SystemMessage,
    TagFilterForm,
    TagForm,
    TagModel,
    UserMessage,
)


class ChatsClient(BaseClient):
    """Client for interacting with OpenWebUI chat API endpoints.

    Provides methods for creating, listing, updating, and managing chats
    including messages, tags, and sharing capabilities.

    Example:
        ```python
        from sdk import OpenWebuiClient
        import asyncio

        async def manage_chats():
            client = OpenWebuiClient(token="your-token")

            # Create a new chat
            new_chat = await client.chats.create_chat(
                title="New Conversation",
                messages=[
                    UserMessage(content="Hello, how can you help me today?")
                ]
            )

            # List all chats
            chats = await client.chats.get_chats_list()

            # Search chats
            results = await client.chats.search_chats("knowledge base")

        asyncio.run(manage_chats())
        ```
    """

    async def get_chats_list(self, page: Optional[int] = None) -> List[ChatTitleIdResponse]:
        """Get list of all user's chats with basic information"""
        params = {"page": page} if page is not None else None
        response = await self.get("/api/v1/chats/", params=params)
        return [ChatTitleIdResponse.model_validate(chat) for chat in response.json()]

    async def delete_all_chats(self) -> bool:
        """Delete all user's chats"""
        response = await self.delete("/api/v1/chats/")
        return response.json()

    async def create_chat(
        self,
        title: str,
        messages: List[ChatMessageType],
        model: str,
    ) -> ChatResponse:
        """Create a new chat with optional initial messages"""
        # Create a properly structured chat data
        chat_data = self.create_chat_data(title=title, messages=messages, model=model)

        # Create the form data
        form_data = ChatForm(chat=chat_data)

        # Send the request
        response = await self.post("/api/v1/chats/new", json_data=form_data.model_dump())
        return ChatResponse.model_validate(response.json())

    async def import_chat(
        self,
        chat_data: ChatData,
        meta: Optional[Dict[str, Any]] = None,
        pinned: bool = False,
        folder_id: Optional[str] = None,
    ) -> ChatResponse:
        """Import an existing chat with full data structure"""
        form_data = ChatImportForm(chat=chat_data, meta=meta, pinned=pinned, folder_id=folder_id)

        response = await self.post("/api/v1/chats/import", json_data=form_data.model_dump())
        return ChatResponse.model_validate(response.json())

    async def search_chats(self, query: str, page: Optional[int] = None) -> List[ChatTitleIdResponse]:
        """Search chats by text or tags (use 'tag:tagname' format for tags)"""
        params = {"text": query}
        if page is not None:
            params["page"] = page

        response = await self.get("/api/v1/chats/search", params=params)
        return [ChatTitleIdResponse.model_validate(chat) for chat in response.json()]

    async def get_chats_by_folder(self, folder_id: str) -> List[ChatResponse]:
        """Get all chats in a specific folder"""
        response = await self.get(f"/api/v1/chats/folder/{folder_id}")
        return [ChatResponse.model_validate(chat) for chat in response.json()]

    async def get_pinned_chats(self) -> List[ChatResponse]:
        """Get all pinned chats"""
        response = await self.get("/api/v1/chats/pinned")
        return [ChatResponse.model_validate(chat) for chat in response.json()]

    async def get_all_chats(self) -> List[ChatResponse]:
        """Get all chats with full details"""
        response = await self.get("/api/v1/chats/all")
        return [ChatResponse.model_validate(chat) for chat in response.json()]

    async def get_archived_chats(self) -> List[ChatResponse]:
        """Get all archived chats"""
        response = await self.get("/api/v1/chats/all/archived")
        return [ChatResponse.model_validate(chat) for chat in response.json()]

    async def get_all_tags(self) -> List[TagModel]:
        """Get all tags created by the user"""
        response = await self.get("/api/v1/chats/all/tags")
        return [TagModel.model_validate(tag) for tag in response.json()]

    async def get_archived_chat_list(self, skip: int = 0, limit: int = 50) -> List[ChatTitleIdResponse]:
        """Get list of archived chats with pagination"""
        params = {"skip": skip, "limit": limit}
        response = await self.get("/api/v1/chats/archived", params=params)
        return [ChatTitleIdResponse.model_validate(chat) for chat in response.json()]

    async def archive_all_chats(self) -> bool:
        """Archive all chats"""
        response = await self.post("/api/v1/chats/archive/all")
        return response.json()

    async def get_shared_chat(self, share_id: str) -> ChatResponse:
        """Get a shared chat by its share ID"""
        response = await self.get(f"/api/v1/chats/share/{share_id}")
        return ChatResponse.model_validate(response.json())

    async def get_chats_by_tag(self, tag_name: str, skip: int = 0, limit: int = 50) -> List[ChatTitleIdResponse]:
        """Get chats filtered by tag name"""
        form_data = TagFilterForm(name=tag_name, skip=skip, limit=limit)
        response = await self.post("/api/v1/chats/tags", json_data=form_data.model_dump())
        return [ChatTitleIdResponse.model_validate(chat) for chat in response.json()]

    async def get_chat(self, chat_id: str) -> ChatResponse:
        """Get a chat by its ID"""
        response = await self.get(f"/api/v1/chats/{chat_id}")
        return ChatResponse.model_validate(response.json())

    async def update_chat(self, chat_id: str, chat_data: ChatData) -> ChatResponse:
        """Update a chat's data"""
        form_data = ChatForm(chat=chat_data)
        response = await self.post(f"/api/v1/chats/{chat_id}", json_data=form_data.model_dump())
        return ChatResponse.model_validate(response.json())

    async def update_message(self, chat_id: str, message_id: str, content: str) -> ChatResponse:
        """Update a specific message in a chat"""
        form_data = MessageForm(content=content)
        response = await self.post(f"/api/v1/chats/{chat_id}/messages/{message_id}", json_data=form_data.model_dump())
        return ChatResponse.model_validate(response.json())

    async def send_message_event(
        self, chat_id: str, message_id: str, event_type: str, event_data: Dict[str, Any]
    ) -> bool:
        """Send an event for a specific message"""
        form_data = EventForm(type=event_type, data=event_data)
        response = await self.post(
            f"/api/v1/chats/{chat_id}/messages/{message_id}/event", json_data=form_data.model_dump()
        )
        return response.json()

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat by its ID"""
        response = await self.delete(f"/api/v1/chats/{chat_id}")
        return response.json()

    async def get_pinned_status(self, chat_id: str) -> bool:
        """Check if a chat is pinned"""
        response = await self.get(f"/api/v1/chats/{chat_id}/pinned")
        return response.json()

    async def toggle_pin(self, chat_id: str) -> ChatResponse:
        """Toggle the pinned status of a chat"""
        response = await self.post(f"/api/v1/chats/{chat_id}/pin")
        return ChatResponse.model_validate(response.json())

    async def clone_chat(self, chat_id: str, title: Optional[str] = None) -> ChatResponse:
        """Clone an existing chat with optional new title"""
        form_data = CloneForm(title=title)
        response = await self.post(f"/api/v1/chats/{chat_id}/clone", json_data=form_data.model_dump())
        return ChatResponse.model_validate(response.json())

    async def clone_shared_chat(self, share_id: str) -> ChatResponse:
        """Clone a shared chat into the user's account"""
        response = await self.post(f"/api/v1/chats/{share_id}/clone/shared")
        return ChatResponse.model_validate(response.json())

    async def toggle_archive(self, chat_id: str) -> ChatResponse:
        """Toggle the archived status of a chat"""
        response = await self.post(f"/api/v1/chats/{chat_id}/archive")
        return ChatResponse.model_validate(response.json())

    async def share_chat(self, chat_id: str) -> ChatResponse:
        """Create or update a shareable version of a chat"""
        response = await self.post(f"/api/v1/chats/{chat_id}/share")
        return ChatResponse.model_validate(response.json())

    async def unshare_chat(self, chat_id: str) -> bool:
        """Stop sharing a previously shared chat"""
        response = await self.delete(f"/api/v1/chats/{chat_id}/share")
        return response.json()

    async def update_chat_folder(self, chat_id: str, folder_id: Optional[str] = None) -> ChatResponse:
        """Move a chat to a different folder"""
        form_data = ChatFolderIdForm(folder_id=folder_id)
        response = await self.post(f"/api/v1/chats/{chat_id}/folder", json_data=form_data.model_dump())
        return ChatResponse.model_validate(response.json())

    async def get_chat_tags(self, chat_id: str) -> List[TagModel]:
        """Get all tags associated with a chat"""
        response = await self.get(f"/api/v1/chats/{chat_id}/tags")
        return [TagModel.model_validate(tag) for tag in response.json()]

    async def add_tag(self, chat_id: str, tag_name: str) -> List[TagModel]:
        """Add a tag to a chat"""
        form_data = TagForm(name=tag_name)
        response = await self.post(f"/api/v1/chats/{chat_id}/tags", json_data=form_data.model_dump())
        return [TagModel.model_validate(tag) for tag in response.json()]

    async def remove_tag(self, chat_id: str, tag_name: str) -> List[TagModel]:
        """Remove a tag from a chat"""
        form_data = TagForm(name=tag_name)
        response = await self.delete(f"/api/v1/chats/{chat_id}/tags", json_data=form_data.model_dump())
        return [TagModel.model_validate(tag) for tag in response.json()]

    async def remove_all_tags(self, chat_id: str) -> bool:
        """Remove all tags from a chat"""
        response = await self.delete(f"/api/v1/chats/{chat_id}/tags/all")
        return response.json()

    def create_chat_data(
        self,
        title: str,
        messages: List[ChatMessageType],
        model: str,
    ) -> ChatData:
        """Create a properly structured chat data object for API requests"""
        # Initialize chat structure
        messages_dict = {}
        messages_list = []
        last_id = ""
        models_list = [model] if model else []
        current_timestamp = int(datetime.now().timestamp())

        # Add messages if provided
        parent_id = None

        for i, msg in enumerate(messages or []):
            # It's a BaseMessage or subclass
            msg_id = msg.id or str(uuid.uuid4())
            msg.id = msg_id

            # Set timestamp if not provided
            if not msg.timestamp:
                msg.timestamp = current_timestamp

            # Set parent ID if not provided and we have one
            if not msg.parentId and parent_id is not None:
                msg.parentId = parent_id

            # Add model info for user messages if provided
            if msg.role == "user" and model and not msg.models:
                msg.models = models_list

            if msg.role == "assistant" and model and not msg.model:
                msg.model = model
                msg.modelName = model

            # Store the message in both formats (dict and list)
            messages_dict[msg_id] = ChatMessageContent.model_validate(msg.model_dump())
            messages_list.append(msg.model_dump())

            # Update parent for next message in the chain
            parent_id = msg_id
            # Update last ID to the most recent message
            last_id = msg_id

        # Create history with currentId pointing to last message
        history = ChatHistory(messages=messages_dict, currentId=last_id)

        # Create timestamp if not provided
        timestamp = int(datetime.now().timestamp() * 1000)  # API uses milliseconds

        # Return a properly structured ChatData object
        return ChatData(
            title=title,
            history=history,
            messages=messages_list,
            models=models_list,
            params={},
            tags=[],
            timestamp=timestamp,
            files=[],
        )

    # Helper methods for creating chat messages

    def create_user_message(self, content: str, models: Optional[List[str]] = None) -> UserMessage:
        """Create a properly structured user message"""
        return UserMessage(
            id=str(uuid.uuid4()), content=content, timestamp=int(datetime.now().timestamp()), models=models
        )

    def create_assistant_message(
        self,
        content: str,
        model: Optional[str] = None,
        model_name: Optional[str] = None,
        parent_id: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> AssistantMessage:
        """Create a properly structured assistant message"""
        return AssistantMessage(
            id=str(uuid.uuid4()),
            content=content,
            timestamp=int(datetime.now().timestamp()),
            parentId=parent_id,
            model=model,
            modelName=model_name,
            tool_calls=tool_calls,
        )

    def create_system_message(self, content: str) -> SystemMessage:
        """Create a properly structured system message"""
        return SystemMessage(id=str(uuid.uuid4()), content=content, timestamp=int(datetime.now().timestamp()))
