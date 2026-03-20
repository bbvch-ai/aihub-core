from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.bot.runners.bot_runner import BotRunner
    from swiss_ai_hub.bot.runners.bot_test_runner import BotTestRunner
    from swiss_ai_hub.bot.runners.simulated_agent_bot_test_runner import SimulatedAgentBotTestRunner

__all__ = [
    "BotRunner",
    "BotTestRunner",
    "SimulatedAgentBotTestRunner",
]

_LAZY_IMPORTS: dict[str, str] = {
    "BotRunner": "swiss_ai_hub.bot.runners.bot_runner",
    "BotTestRunner": "swiss_ai_hub.bot.runners.bot_test_runner",
    "SimulatedAgentBotTestRunner": "swiss_ai_hub.bot.runners.simulated_agent_bot_test_runner",
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
