from typing import Annotated, Self

from aihub_lib.agents.AgentRef import AgentRef
from aihub_lib.nats.events.form.elements.AgentSelector import AgentSelector
from aihub_lib.nats.events.form.Form import Form
from pydantic import Field

from aihub_agent.agents.RagAgent.events import NamespaceAwareUserMessageEvent
from aihub_agent.i18n.AgentLocaleString import AgentLocaleString


class RAGDelegationConfig(Form):
    """
    Configuration for delegating queries to a RAG agent.

    Uses AgentSelector filtered to agents that accept NamespaceAwareUserMessageEvent.
    """

    rag_agent: Annotated[
        AgentRef | AgentSelector,
        Field(description="The target RAG agent to delegate queries to."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RAGDelegationConfig."""
        return cls(
            rag_agent=AgentSelector(
                label=AgentLocaleString.from_i18n_path(
                    "agent.namespace_selection_agent.delegation_config.rag_agent.label"
                ),
                help=AgentLocaleString.from_i18n_path(
                    "agent.namespace_selection_agent.delegation_config.rag_agent.help"
                ),
                start_event=NamespaceAwareUserMessageEvent.event_name_from_class(),
                class_placeholder=AgentLocaleString.from_i18n_path(
                    "agent.namespace_selection_agent.delegation_config.rag_agent.class_placeholder"
                ),
                id_placeholder=AgentLocaleString.from_i18n_path(
                    "agent.namespace_selection_agent.delegation_config.rag_agent.id_placeholder"
                ),
            ),
        )
