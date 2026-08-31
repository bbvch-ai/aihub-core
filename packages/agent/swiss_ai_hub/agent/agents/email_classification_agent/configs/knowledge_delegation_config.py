from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.form import AgentSelector
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.agents.rag_agent.events import RAGStartEvent
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class KnowledgeDelegationConfig(Form):
    """The RAG agent that answers a classified message from its category's collection.

    Delegation rather than retrieval in this blueprint: the RAG agent already owns the retrievers, the reranking, the
    context-sufficiency guard and the answer prompt, and reimplementing any of that here would be a second, worse copy
    that drifts. What this blueprint contributes is the one thing the RAG agent cannot know — which collection answers
    this particular message, which is exactly what the classification verdict decided.

    Filtered to agents that accept `RAGStartEvent`, following `RAGDelegationConfig` on the namespace selection agent —
    that event is what carries `selected_namespaces`, so an agent that does not accept it cannot be scoped to one
    collection and must not be offered here.
    """

    rag_agent: Annotated[
        AgentRef | AgentSelector,
        Field(description="The RAG agent that answers a message from its category's collection."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            rag_agent=AgentSelector(
                label=AgentLocaleString.from_i18n_path("agent.email_classification_agent.config.rag_agent.label"),
                help=AgentLocaleString.from_i18n_path("agent.email_classification_agent.config.rag_agent.help"),
                start_event=RAGStartEvent.event_name_from_class(),
                class_placeholder=AgentLocaleString.from_i18n_path(
                    "agent.email_classification_agent.config.rag_agent.class_placeholder"
                ),
                id_placeholder=AgentLocaleString.from_i18n_path(
                    "agent.email_classification_agent.config.rag_agent.id_placeholder"
                ),
            ),
        )
