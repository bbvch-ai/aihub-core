from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.bot.persistence.entities.conversation_entity import ConversationEntity, ConversationTracker
    from swiss_ai_hub.bot.persistence.entities.path_entity import Credentials, PathEntity

__all__ = [
    "ConversationEntity",
    "ConversationTracker",
    "Credentials",
    "PathEntity",
]

_LAZY_IMPORTS: dict[str, str] = {
    "ConversationEntity": "swiss_ai_hub.bot.persistence.entities.conversation_entity",
    "ConversationTracker": "swiss_ai_hub.bot.persistence.entities.conversation_entity",
    "Credentials": "swiss_ai_hub.bot.persistence.entities.path_entity",
    "PathEntity": "swiss_ai_hub.bot.persistence.entities.path_entity",
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
