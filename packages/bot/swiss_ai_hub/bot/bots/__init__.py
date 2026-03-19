from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.bot.bots.bot_in_the_loop.bot_in_the_loop_bot import BotInTheLoopBot
    from swiss_ai_hub.bot.bots.chat.agent.agent_chat_bot import AgentChatBot
    from swiss_ai_hub.bot.bots.chat.agent.stream_agent_chat_bot import StreamAgentChatBot
    from swiss_ai_hub.bot.bots.chat.base_chat_bot import BaseChatBot
    from swiss_ai_hub.bot.bots.chat.completion_handler import CompletionHandler
    from swiss_ai_hub.bot.bots.chat.openai.openai_chat_bot import OpenaiChatBot
    from swiss_ai_hub.bot.bots.chat.openai.stream_openai_chat_bot import StreamOpenaiChatBot

__all__ = [
    "AgentChatBot",
    "BaseChatBot",
    "BotInTheLoopBot",
    "CompletionHandler",
    "OpenaiChatBot",
    "StreamAgentChatBot",
    "StreamOpenaiChatBot",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentChatBot": "swiss_ai_hub.bot.bots.chat.agent.agent_chat_bot",
    "BaseChatBot": "swiss_ai_hub.bot.bots.chat.base_chat_bot",
    "BotInTheLoopBot": "swiss_ai_hub.bot.bots.bot_in_the_loop.bot_in_the_loop_bot",
    "CompletionHandler": "swiss_ai_hub.bot.bots.chat.completion_handler",
    "OpenaiChatBot": "swiss_ai_hub.bot.bots.chat.openai.openai_chat_bot",
    "StreamAgentChatBot": "swiss_ai_hub.bot.bots.chat.agent.stream_agent_chat_bot",
    "StreamOpenaiChatBot": "swiss_ai_hub.bot.bots.chat.openai.stream_openai_chat_bot",
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
