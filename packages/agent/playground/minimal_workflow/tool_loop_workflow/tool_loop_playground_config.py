from typing import Self

from swiss_ai_hub.core.agents import AgentConfig

from swiss_ai_hub.agent.capabilities import ConversationFields, ToolLoopFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields


class ToolLoopPlaygroundConfig(KnowledgeFields, ToolLoopFields, ConversationFields, AgentConfig):
    """The collections the knowledge tool may search and the answering model; the loop's own settings are published
    by the runner with the blueprint's tools as options."""

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            **cls.conversation_form_elements(),
            **cls.knowledge_form_elements(),
        )
