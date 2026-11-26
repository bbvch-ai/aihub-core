from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.ee.agents.email_classification_agent.configs.email_classification_agent_config import (
        EmailClassificationAgentConfig,
    )
    from swiss_ai_hub.ee.agents.email_classification_agent.email_classification_agent import (
        EmailClassificationAgent,
    )
    from swiss_ai_hub.ee.agents.universal_agent.universal_agent import UniversalAgent
    from swiss_ai_hub.ee.agents.universal_agent.universal_agent_config import UniversalAgentConfig
    from swiss_ai_hub.ee.i18n.enterprise_locale_handler import EnterpriseLocaleHandler
    from swiss_ai_hub.ee.i18n.enterprise_locale_string import EnterpriseLocaleString

__all__ = [
    "EmailClassificationAgent",
    "EmailClassificationAgentConfig",
    "EnterpriseLocaleHandler",
    "EnterpriseLocaleString",
    "UniversalAgent",
    "UniversalAgentConfig",
]

_LAZY_IMPORTS: dict[str, str] = {
    "EmailClassificationAgent": "swiss_ai_hub.ee.agents.email_classification_agent.email_classification_agent",
    "EmailClassificationAgentConfig": (
        "swiss_ai_hub.ee.agents.email_classification_agent.configs.email_classification_agent_config"
    ),
    "EnterpriseLocaleHandler": "swiss_ai_hub.ee.i18n.enterprise_locale_handler",
    "EnterpriseLocaleString": "swiss_ai_hub.ee.i18n.enterprise_locale_string",
    "UniversalAgent": "swiss_ai_hub.ee.agents.universal_agent.universal_agent",
    "UniversalAgentConfig": "swiss_ai_hub.ee.agents.universal_agent.universal_agent_config",
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
