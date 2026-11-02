from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.form import AgentSelector
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class KnowledgeDelegationConfig(Form):
    """The RAG agent that answers a classified message from its category's collection.

    Delegation rather than retrieval in this blueprint: the RAG agent already owns the retrievers, the reranking, the
    context-sufficiency guard and the answer prompt, and reimplementing any of that here would be a second, worse copy
    that drifts. What this blueprint contributes is the one thing the RAG agent cannot know — which collection answers
    this particular message, which is exactly what the classification verdict decided.

    Pinned to `RAGAgent` rather than filtered by start event. Accepting `RAGStartEvent` is necessary but not
    sufficient: `ExpertRAGAgent` accepts it too, and offering a blueprint whose expert-escalation path waits on a human
    turns a mailbox run into one that blocks on somebody answering. The class is not an admin decision here, so the
    class dropdown is not rendered and only RAG agent profiles are listed.
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
                agent_class=RAGAgent.__name__,
                id_placeholder=AgentLocaleString.from_i18n_path(
                    "agent.email_classification_agent.config.rag_agent.id_placeholder"
                ),
            ),
        )
