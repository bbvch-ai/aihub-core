from typing import Self

from playground.minimal_workflow.tool_loop_workflow.playground_tools import PlaygroundTools
from swiss_ai_hub.core.agents import AgentConfig

from swiss_ai_hub.agent.capabilities import ConversationFields, ToolLoop, ToolLoopFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields


class ToolLoopPlaygroundConfig(KnowledgeFields, ToolLoopFields, ConversationFields, AgentConfig):
    """The loop's limits and approvals, the collections the knowledge tool may search, and the answering model."""

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
            **cls.tool_loop_form_elements(ToolLoop.names(PlaygroundTools.ALL)),
        )
