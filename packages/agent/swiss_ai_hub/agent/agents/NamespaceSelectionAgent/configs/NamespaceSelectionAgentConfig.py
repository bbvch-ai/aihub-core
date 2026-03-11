from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents.AgentConfig import AgentConfig
from swiss_ai_hub.core.form.constraints import Ge, MinLen
from swiss_ai_hub.core.form.elements.InputNumber import InputNumber
from swiss_ai_hub.core.form.elements.KnowledgeDatabaseSelector import KnowledgeDatabaseSelector
from swiss_ai_hub.core.form.elements.LocaleInput import LocaleInput
from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from swiss_ai_hub.core.i18n.LocaleString import LocaleString

from swiss_ai_hub.agent.agents.NamespaceSelectionAgent.configs.RAGDelegationConfig import RAGDelegationConfig
from swiss_ai_hub.agent.i18n.AgentLocaleString import AgentLocaleString


class NamespaceSelectionAgentConfig(AgentConfig):
    """
    Configuration for NamespaceSelectionAgent.

    This agent uses an LLM to determine which namespaces to query based on the
    user's first message. It asks follow-up questions if needed, then requests
    user approval before storing the selection and delegating to a RAG agent.

    Supports duality pattern for form rendering and data validation.
    """

    llm: Annotated[
        LLMConfig,
        Field(description="LLM configuration for namespace determination."),
    ]

    bucket_names: Annotated[
        list[str] | KnowledgeDatabaseSelector,
        Field(description="List of knowledge databases to fetch namespaces from.", title="Knowledge Databases"),
        MinLen(1),
    ]

    rag_delegation: Annotated[
        RAGDelegationConfig,
        Field(description="Configuration for delegating queries to the RAG agent.", title="RAG Delegation"),
    ]

    max_conversation_history_entries: Annotated[
        int | InputNumber,
        Field(default=20, description="Max conversation history entries to keep. Keeps first entry + most recent."),
        Ge(4),
    ]

    approval_message_template: Annotated[
        LocaleString | LocaleInput,
        Field(description="Message template for namespace approval. Use {namespaces} placeholder."),
    ] = AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.defaults.approval_message_template")

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode NamespaceSelectionAgentConfig."""
        base = AgentConfig.as_form()

        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            llm=LLMConfig.as_form(),
            bucket_names=KnowledgeDatabaseSelector(
                label=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.config.bucket_names.label"),
                help=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.config.bucket_names.help"),
            ),
            rag_delegation=RAGDelegationConfig.as_form(),
            max_conversation_history_entries=InputNumber(
                label=AgentLocaleString.from_i18n_path(
                    "agent.namespace_selection_agent.config.max_conversation_history_entries.label"
                ),
                min=4,
                max=100,
                step=1,
            ),
            approval_message_template=LocaleString.as_form(
                label=AgentLocaleString.from_i18n_path(
                    "agent.namespace_selection_agent.config.approval_message_template.label"
                ),
                input_type="textarea",
            ),
        )
