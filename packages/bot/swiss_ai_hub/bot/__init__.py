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
    from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController
    from swiss_ai_hub.bot.routes.bot_in_the_loop.bot_in_the_loop_controller import BotInTheLoopController
    from swiss_ai_hub.bot.routes.openai.openai_chat_controller import OpenaiChatController
    from swiss_ai_hub.bot.runners.bot_runner import BotRunner
    from swiss_ai_hub.bot.runners.bot_test_runner import BotTestRunner
    from swiss_ai_hub.bot.runners.simulated_agent_bot_test_runner import SimulatedAgentBotTestRunner

__all__ = [
    "AgentChatBot",
    "AgentChatController",
    "BaseChatBot",
    "BotInTheLoopBot",
    "BotInTheLoopController",
    "BotRunner",
    "BotTestRunner",
    "CompletionHandler",
    "OpenaiChatBot",
    "OpenaiChatController",
    "SimulatedAgentBotTestRunner",
    "StreamAgentChatBot",
    "StreamOpenaiChatBot",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentChatBot": "swiss_ai_hub.bot.bots.chat.agent.agent_chat_bot",
    "AgentChatController": "swiss_ai_hub.bot.routes.agent.agent_chat_controller",
    "BaseChatBot": "swiss_ai_hub.bot.bots.chat.base_chat_bot",
    "BotInTheLoopBot": "swiss_ai_hub.bot.bots.bot_in_the_loop.bot_in_the_loop_bot",
    "BotInTheLoopController": "swiss_ai_hub.bot.routes.bot_in_the_loop.bot_in_the_loop_controller",
    "BotRunner": "swiss_ai_hub.bot.runners.bot_runner",
    "BotTestRunner": "swiss_ai_hub.bot.runners.bot_test_runner",
    "CompletionHandler": "swiss_ai_hub.bot.bots.chat.completion_handler",
    "OpenaiChatBot": "swiss_ai_hub.bot.bots.chat.openai.openai_chat_bot",
    "OpenaiChatController": "swiss_ai_hub.bot.routes.openai.openai_chat_controller",
    "SimulatedAgentBotTestRunner": "swiss_ai_hub.bot.runners.simulated_agent_bot_test_runner",
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
