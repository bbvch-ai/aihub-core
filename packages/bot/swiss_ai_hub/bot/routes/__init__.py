from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController
    from swiss_ai_hub.bot.routes.bot_in_the_loop.bot_in_the_loop_controller import BotInTheLoopController
    from swiss_ai_hub.bot.routes.openai.openai_chat_controller import OpenaiChatController
    from swiss_ai_hub.bot.routes.routes_service import RoutesService

__all__ = [
    "AgentChatController",
    "BotInTheLoopController",
    "OpenaiChatController",
    "RoutesService",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentChatController": "swiss_ai_hub.bot.routes.agent.agent_chat_controller",
    "BotInTheLoopController": "swiss_ai_hub.bot.routes.bot_in_the_loop.bot_in_the_loop_controller",
    "OpenaiChatController": "swiss_ai_hub.bot.routes.openai.openai_chat_controller",
    "RoutesService": "swiss_ai_hub.bot.routes.routes_service",
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
