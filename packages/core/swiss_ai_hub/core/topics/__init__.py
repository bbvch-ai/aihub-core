from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.topics.discovery.agent.agent_class_discovery_topic import AgentClassDiscoveryTopic
    from swiss_ai_hub.core.topics.process.process_class_topic import ProcessClassTopic
    from swiss_ai_hub.core.topics import Topic

__all__ = [
    "Topic",
    "AgentClassDiscoveryTopic",
    "ProcessClassTopic",
]

_LAZY_IMPORTS = {
    "Topic": "swiss_ai_hub.core.topics",
    "AgentClassDiscoveryTopic": "swiss_ai_hub.core.topics.discovery.agent.agent_class_discovery_topic",
    "ProcessClassTopic": "swiss_ai_hub.core.topics.process.process_class_topic",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
