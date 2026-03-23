from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.form import AgentSelector
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.agents.rag_agent.events import NamespaceAwareUserMessageEvent
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


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
