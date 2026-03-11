from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents.AgentRef import AgentRef
from swiss_ai_hub.core.form.elements.AgentSelector import AgentSelector
from swiss_ai_hub.core.form.Form import Form

from swiss_ai_hub.agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from swiss_ai_hub.agent.i18n.AgentLocaleString import AgentLocaleString


class ExpertEscalationConfig(Form):
    """
    Configuration for expert escalation workflow.

    When configured in RAGAgentConfig, this enables the agent to offer expert
    escalation when retrieved context is insufficient to answer the user's query.

    Uses AgentSelector for cascading agent class/ID selection with automatic
    filtering to only show agents that accept AskExpertStartEvent.

    Supports duality pattern for form rendering and data validation.
    """

    agent: Annotated[
        AgentRef | AgentSelector,
        Field(description="The agent to escalate to when context is insufficient."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode ExpertEscalationConfig."""
        return cls(
            agent=AgentSelector(
                label=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.config.agent.label"),
                help=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.config.agent.help"),
                start_event=AskExpertStartEvent.event_name_from_class(),
            ),
        )
