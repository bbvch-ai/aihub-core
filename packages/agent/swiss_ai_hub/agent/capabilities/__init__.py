from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.capabilities.capability import Capability
    from swiss_ai_hub.agent.capabilities.conversation.conversation_capability import ConversationCapability
    from swiss_ai_hub.agent.capabilities.conversation.conversational_agent_config import ConversationalAgentConfig
    from swiss_ai_hub.agent.capabilities.memory.memory_capability import MemoryCapability
    from swiss_ai_hub.agent.capabilities.memory.memory_enabled_agent_config import MemoryEnabledAgentConfig
    from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig
    from swiss_ai_hub.agent.capabilities.self_awareness.self_awareness_capability import SelfAwarenessCapability

__all__ = [
    "Capability",
    "ConversationCapability",
    "ConversationalAgentConfig",
    "MemoryCapability",
    "MemoryEnabledAgentConfig",
    "SelfAwarenessCapability",
    "UserMemoryConfig",
]

_LAZY_IMPORTS: dict[str, str] = {
    "Capability": "swiss_ai_hub.agent.capabilities.capability",
    "ConversationCapability": "swiss_ai_hub.agent.capabilities.conversation.conversation_capability",
    "ConversationalAgentConfig": "swiss_ai_hub.agent.capabilities.conversation.conversational_agent_config",
    "MemoryCapability": "swiss_ai_hub.agent.capabilities.memory.memory_capability",
    "MemoryEnabledAgentConfig": "swiss_ai_hub.agent.capabilities.memory.memory_enabled_agent_config",
    "SelfAwarenessCapability": "swiss_ai_hub.agent.capabilities.self_awareness.self_awareness_capability",
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
