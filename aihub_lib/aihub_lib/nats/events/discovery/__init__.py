# Lazy imports to avoid circular dependency with AgentConfig


def __getattr__(name: str):
    if name == "ProcessClassDiscoveryResponseEvent":
        from .process import ProcessClassDiscoveryResponseEvent

        return ProcessClassDiscoveryResponseEvent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ProcessClassDiscoveryResponseEvent",
]
