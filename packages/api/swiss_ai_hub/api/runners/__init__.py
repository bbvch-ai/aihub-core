from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.runners.api_runner import ApiRunner
    from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner
    from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner
    from swiss_ai_hub.api.runners.simulation.process.simulated_process_api_test_runner import (
        SimulatedProcessApiTestRunner,
    )

__all__ = [
    "ApiRunner",
    "ApiTestRunner",
    "SimulatedAgentApiTestRunner",
    "SimulatedProcessApiTestRunner",
]

_LAZY_IMPORTS: dict[str, str] = {
    "ApiRunner": "swiss_ai_hub.api.runners.api_runner",
    "ApiTestRunner": "swiss_ai_hub.api.runners.api_test_runner",
    "SimulatedAgentApiTestRunner": "swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner",
    "SimulatedProcessApiTestRunner": "swiss_ai_hub.api.runners.simulation.process.simulated_process_api_test_runner",
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
