from swiss_ai_hub.core.events.agent import RAGStartEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import OrgMemoryReadConfig


class ExpertWriteNamespace:
    """The organization-memory namespace an expert's answer is written under."""

    @staticmethod
    def resolve(event: UserMessageEvent | RAGStartEvent, org_memory: OrgMemoryReadConfig | None) -> str | None:
        """A single-entry override on the start event propagates; several or none fall back to the profile's
        default, because a write goes to one namespace."""
        default = org_memory.default_tenant_namespace if org_memory else None
        if not isinstance(event, RAGStartEvent):
            return default
        requested = event.org_memory_namespaces
        if len(requested) == 1:
            return requested[0]
        return default
