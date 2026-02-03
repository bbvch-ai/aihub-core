from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.NamespaceSelectionAgent.configs.RAGDelegationConfig import RAGDelegationConfig


class NamespaceSelectionAgentConfig(AgentConfig):
    """Configuration for NamespaceSelectionAgent.

    This agent uses an LLM to determine which namespaces to query based on the
    user's first message. It asks follow-up questions if needed, then requests
    user approval before storing the selection and delegating to a RAG agent.
    """

    llm: Annotated[
        LLMConfig,
        Field(description="LLM configuration for namespace determination."),
    ]

    bucket_names: Annotated[
        list[str],
        Field(description="List of bucket names to fetch namespaces from.", min_length=1),
    ]

    rag_delegation: Annotated[
        RAGDelegationConfig,
        Field(description="Configuration for delegating queries to the RAG agent."),
    ]

    max_conversation_history_entries: Annotated[
        int,
        Field(
            default=20,
            ge=4,
            description="Maximum number of conversation history entries to keep. Keeps first entry + most recent.",
        ),
    ]

    approval_message_template: Annotated[
        LocaleString,
        Field(description="Message template for namespace approval. Use {namespaces} placeholder."),
    ] = LocaleString(
        en=(
            "Based on your request, I suggest querying the following knowledge sources:\n\n"
            "{namespaces}\n\n"
            "Do you approve this selection?"
        ),
        de=(
            "Basierend auf Ihrer Anfrage schlage ich vor, folgende Wissensquellen abzufragen:\n\n"
            "{namespaces}\n\n"
            "Genehmigen Sie diese Auswahl?"
        ),
        fr=(
            "Sur la base de votre demande, je suggère d'interroger les sources de connaissances "
            "suivantes :\n\n"
            "{namespaces}\n\n"
            "Approuvez-vous cette sélection ?"
        ),
        it=(
            "In base alla tua richiesta, suggerisco di interrogare le seguenti fonti di "
            "conoscenza:\n\n"
            "{namespaces}\n\n"
            "Approvi questa selezione?"
        ),
    )
