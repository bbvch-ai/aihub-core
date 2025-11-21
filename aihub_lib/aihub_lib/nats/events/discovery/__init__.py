# Lazy imports to avoid circular dependency with AgentConfig


def __getattr__(name: str):
    if name == "AgentInstanceDiscoveryResponseEvent":
        from .agent import AgentInstanceDiscoveryResponseEvent

        return AgentInstanceDiscoveryResponseEvent
    elif name == "InstanceDiscoveryRequestEvent":
        from .InstanceDiscoveryRequestEvent import InstanceDiscoveryRequestEvent

        return InstanceDiscoveryRequestEvent
    elif name == "ProcessClassDiscoveryResponseEvent":
        from .process import ProcessClassDiscoveryResponseEvent

        return ProcessClassDiscoveryResponseEvent
    elif name == "ProcessInstanceDiscoveryResponseEvent":
        from .process import ProcessInstanceDiscoveryResponseEvent

        return ProcessInstanceDiscoveryResponseEvent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AgentInstanceDiscoveryResponseEvent",
    "ProcessClassDiscoveryResponseEvent",
    "ProcessInstanceDiscoveryResponseEvent",
    "InstanceDiscoveryRequestEvent",
]
