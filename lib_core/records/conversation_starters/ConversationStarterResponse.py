from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator


class ConversationMessages(BaseModel):
    """
    Represents a single message in a conversation.
    """

    role: str = Field(
        ...,
        description="Role of the message sender (e.g., 'user', 'assistant')",
        example="user",
    )
    content: str = Field(
        ...,
        description="Content of the message",
        example="Hello, how can I help you today?",
    )
    name: Optional[str] = Field(
        None,
        description="Optional name of the message sender",
        example="John Doe",
    )


class ConversationStarterResponse(BaseModel):
    """
    Represents the response for starting a conversation, including details about the participants and initial messages.
    """

    id: str = Field(
        ...,
        alias="_id",
        serialization_alias="id",
        description="Unique identifier for the conversation starter",
        example="507f1f77bcf86cd799439011",
    )
    source_user_email: str = Field(
        ...,
        description="Email of the user initiating the conversation",
        example="source@example.com",
    )
    target_user_email: str = Field(
        ...,
        description="Email of the target user for the conversation",
        example="target@example.com",
    )
    source_agent_id: str = Field(
        ...,
        description="ID of the agent associated with the source user",
        example="123456789",
    )
    target_agent_id: str = Field(
        ...,
        description="ID of the agent associated with the target user",
        example="987654321",
    )
    source_conversation_id: Optional[str] = Field(
        None,
        description="Optional ID of the source conversation",
        example="43219876",
    )
    target_conversation_id: Optional[str] = Field(
        None,
        description="Optional ID of the target conversation",
        example="67891234",
    )
    title: str = Field(
        ...,
        description="Title of the conversation",
        example="Customer Support Inquiry",
    )
    messages: List[ConversationMessages] = Field(..., description="List of initial messages in the conversation")

    @field_validator("id", mode="before")
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        populate_by_name = True
        use_aliases = True
