from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic
    from swiss_ai_hub.core.topics.agents.partial_agent_topic import PartialAgentTopic
    from swiss_ai_hub.core.topics.discovery.agent.agent_class_discovery_topic import AgentClassDiscoveryTopic
    from swiss_ai_hub.core.topics.discovery.discovery_topic import DiscoveryTopic
    from swiss_ai_hub.core.topics.process.process_class_topic import ProcessClassTopic
    from swiss_ai_hub.core.topics.process.process_instance_topic import ProcessInstanceTopic
    from swiss_ai_hub.core.topics.rpc.rpc_topic import RpcTopic
    from swiss_ai_hub.core.topics.topic import Topic

__all__ = [
    "AgentClassDiscoveryTopic",
    "AgentInstanceTopic",
    "DiscoveryTopic",
    "PartialAgentTopic",
    "ProcessClassTopic",
    "ProcessInstanceTopic",
    "RpcTopic",
    "Topic",
]

_LAZY_IMPORTS = {
    "AgentClassDiscoveryTopic": "swiss_ai_hub.core.topics.discovery.agent.agent_class_discovery_topic",
    "AgentInstanceTopic": "swiss_ai_hub.core.topics.agents.agent_instance_topic",
    "DiscoveryTopic": "swiss_ai_hub.core.topics.discovery.discovery_topic",
    "PartialAgentTopic": "swiss_ai_hub.core.topics.agents.partial_agent_topic",
    "ProcessClassTopic": "swiss_ai_hub.core.topics.process.process_class_topic",
    "ProcessInstanceTopic": "swiss_ai_hub.core.topics.process.process_instance_topic",
    "RpcTopic": "swiss_ai_hub.core.topics.rpc.rpc_topic",
    "Topic": "swiss_ai_hub.core.topics.topic",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
