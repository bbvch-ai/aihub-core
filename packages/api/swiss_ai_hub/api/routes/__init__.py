from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
    from swiss_ai_hub.api.routes.auth_provider.auth_provider_controller import AuthProviderController
    from swiss_ai_hub.api.routes.evaluation.dataset_controller import DatasetController
    from swiss_ai_hub.api.routes.event.event_controller import EventController
    from swiss_ai_hub.api.routes.file.file_controller import FileController
    from swiss_ai_hub.api.routes.health.api_health_controller import ApiHealthController
    from swiss_ai_hub.api.routes.i18n.i18n_controller import I18nController
    from swiss_ai_hub.api.routes.knowledge.knowledge_controller import KnowledgeController
    from swiss_ai_hub.api.routes.memory.organization_memory_controller import OrganizationMemoryController
    from swiss_ai_hub.api.routes.memory.user_memory_controller import UserMemoryController
    from swiss_ai_hub.api.routes.model.model_controller import ModelController
    from swiss_ai_hub.api.routes.my_account.my_account_controller import MyAccountController
    from swiss_ai_hub.api.routes.my_tenant.my_tenant_controller import MyTenantController
    from swiss_ai_hub.api.routes.notification.notification_controller import NotificationController
    from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
    from swiss_ai_hub.api.routes.parsing.parsing_controller import ParsingController
    from swiss_ai_hub.api.routes.process.process_controller import ProcessController
    from swiss_ai_hub.api.routes.role.role_controller import RoleController
    from swiss_ai_hub.api.routes.suite.suite_controller import SuiteController
    from swiss_ai_hub.api.routes.thread.thread_controller import ThreadController
    from swiss_ai_hub.api.routes.token.token_controller import TokenController
    from swiss_ai_hub.api.routes.translation.translation_controller import TranslationController
    from swiss_ai_hub.api.routes.user.user_controller import UserController

__all__ = [
    "AgentController",
    "ApiHealthController",
    "AuthProviderController",
    "DatasetController",
    "EventController",
    "FileController",
    "I18nController",
    "KnowledgeController",
    "ModelController",
    "MyAccountController",
    "MyTenantController",
    "NotificationController",
    "OpenaiController",
    "OrganizationMemoryController",
    "ParsingController",
    "ProcessController",
    "RoleController",
    "SuiteController",
    "ThreadController",
    "TokenController",
    "TranslationController",
    "UserController",
    "UserMemoryController",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentController": "swiss_ai_hub.api.routes.agent.agent_controller",
    "ApiHealthController": "swiss_ai_hub.api.routes.health.api_health_controller",
    "AuthProviderController": "swiss_ai_hub.api.routes.auth_provider.auth_provider_controller",
    "DatasetController": "swiss_ai_hub.api.routes.evaluation.dataset_controller",
    "EventController": "swiss_ai_hub.api.routes.event.event_controller",
    "FileController": "swiss_ai_hub.api.routes.file.file_controller",
    "I18nController": "swiss_ai_hub.api.routes.i18n.i18n_controller",
    "KnowledgeController": "swiss_ai_hub.api.routes.knowledge.knowledge_controller",
    "ModelController": "swiss_ai_hub.api.routes.model.model_controller",
    "MyAccountController": "swiss_ai_hub.api.routes.my_account.my_account_controller",
    "MyTenantController": "swiss_ai_hub.api.routes.my_tenant.my_tenant_controller",
    "NotificationController": "swiss_ai_hub.api.routes.notification.notification_controller",
    "OpenaiController": "swiss_ai_hub.api.routes.openai.openai_controller",
    "OrganizationMemoryController": "swiss_ai_hub.api.routes.memory.organization_memory_controller",
    "ParsingController": "swiss_ai_hub.api.routes.parsing.parsing_controller",
    "ProcessController": "swiss_ai_hub.api.routes.process.process_controller",
    "RoleController": "swiss_ai_hub.api.routes.role.role_controller",
    "SuiteController": "swiss_ai_hub.api.routes.suite.suite_controller",
    "ThreadController": "swiss_ai_hub.api.routes.thread.thread_controller",
    "TokenController": "swiss_ai_hub.api.routes.token.token_controller",
    "TranslationController": "swiss_ai_hub.api.routes.translation.translation_controller",
    "UserController": "swiss_ai_hub.api.routes.user.user_controller",
    "UserMemoryController": "swiss_ai_hub.api.routes.memory.user_memory_controller",
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
