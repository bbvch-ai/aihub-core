from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles
    from swiss_ai_hub.agent.capabilities.capability import Capability
    from swiss_ai_hub.agent.capabilities.catalog import CapabilityCatalog
    from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
    from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
    from swiss_ai_hub.agent.capabilities.knowledge.knowledge import Knowledge
    from swiss_ai_hub.agent.capabilities.memory.memory import Memory
    from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
    from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig
    from swiss_ai_hub.agent.capabilities.requested_features import RequestedFeatures

__all__ = [
    "AttachedFiles",
    "Capability",
    "CapabilityCatalog",
    "Conversation",
    "ConversationFields",
    "Knowledge",
    "Memory",
    "MemoryFields",
    "RequestedFeatures",
    "UserMemoryConfig",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AttachedFiles": "swiss_ai_hub.agent.capabilities.attached_files.attached_files",
    "Capability": "swiss_ai_hub.agent.capabilities.capability",
    "CapabilityCatalog": "swiss_ai_hub.agent.capabilities.catalog",
    "Conversation": "swiss_ai_hub.agent.capabilities.conversation.conversation",
    "ConversationFields": "swiss_ai_hub.agent.capabilities.conversation.conversation_fields",
    "Knowledge": "swiss_ai_hub.agent.capabilities.knowledge.knowledge",
    "Memory": "swiss_ai_hub.agent.capabilities.memory.memory",
    "MemoryFields": "swiss_ai_hub.agent.capabilities.memory.memory_fields",
    "RequestedFeatures": "swiss_ai_hub.agent.capabilities.requested_features",
    "UserMemoryConfig": "swiss_ai_hub.agent.capabilities.memory.user_memory_config",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
