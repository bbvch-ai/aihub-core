from typing import Self

from swiss_ai_hub.core.agents import AgentConfig

from swiss_ai_hub.agent.capabilities import ConversationFields


class CodeExecutionPlaygroundConfig(ConversationFields, AgentConfig):
    """Only the conversation's model, for the title and follow-ups; the code runs as written, no model picks it."""

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            **cls.conversation_form_elements(),
        )
