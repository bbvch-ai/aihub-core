from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
    from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
    from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
    from swiss_ai_hub.api.routes.auth_provider.auth_provider_controller import AuthProviderController
    from swiss_ai_hub.api.routes.event.event_controller import EventController
    from swiss_ai_hub.api.routes.health.api_health_controller import ApiHealthController
    from swiss_ai_hub.api.routes.knowledge.knowledge_controller import KnowledgeController
    from swiss_ai_hub.api.routes.my_account.my_account_controller import MyAccountController
    from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
    from swiss_ai_hub.api.routes.process.process_controller import ProcessController
    from swiss_ai_hub.api.routes.role.role_controller import RoleController
    from swiss_ai_hub.api.routes.thread.thread_controller import ThreadController
    from swiss_ai_hub.api.routes.user.user_controller import UserController
    from swiss_ai_hub.api.runners.api_runner import ApiRunner
    from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner
    from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner
    from swiss_ai_hub.api.runners.simulation.process.simulated_process_api_test_runner import (
        SimulatedProcessApiTestRunner,
    )
    from swiss_ai_hub.api.services.model_creation_service import ModelCreationService

__all__ = [
    "AgentController",
    "ApiHealthController",
    "ApiLocaleHandler",
    "ApiLocaleString",
    "ApiRunner",
    "ApiTestRunner",
    "AuthProviderController",
    "EventController",
    "KnowledgeController",
    "ModelCreationService",
    "MyAccountController",
    "OpenaiController",
    "ProcessController",
    "RoleController",
    "SimulatedAgentApiTestRunner",
    "SimulatedProcessApiTestRunner",
    "ThreadController",
    "UserController",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentController": "swiss_ai_hub.api.routes.agent.agent_controller",
    "ApiHealthController": "swiss_ai_hub.api.routes.health.api_health_controller",
    "ApiLocaleHandler": "swiss_ai_hub.api.i18n.api_locale_handler",
    "ApiLocaleString": "swiss_ai_hub.api.i18n.api_locale_string",
    "ApiRunner": "swiss_ai_hub.api.runners.api_runner",
    "ApiTestRunner": "swiss_ai_hub.api.runners.api_test_runner",
    "AuthProviderController": "swiss_ai_hub.api.routes.auth_provider.auth_provider_controller",
    "EventController": "swiss_ai_hub.api.routes.event.event_controller",
    "KnowledgeController": "swiss_ai_hub.api.routes.knowledge.knowledge_controller",
    "ModelCreationService": "swiss_ai_hub.api.services.model_creation_service",
    "MyAccountController": "swiss_ai_hub.api.routes.my_account.my_account_controller",
    "OpenaiController": "swiss_ai_hub.api.routes.openai.openai_controller",
    "ProcessController": "swiss_ai_hub.api.routes.process.process_controller",
    "RoleController": "swiss_ai_hub.api.routes.role.role_controller",
    "SimulatedAgentApiTestRunner": "swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner",
    "SimulatedProcessApiTestRunner": "swiss_ai_hub.api.runners.simulation.process.simulated_process_api_test_runner",
    "ThreadController": "swiss_ai_hub.api.routes.thread.thread_controller",
    "UserController": "swiss_ai_hub.api.routes.user.user_controller",
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
