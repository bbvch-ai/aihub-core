from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings

from swiss_ai_hub.agent.agents.namespace_selection_agent.configs import (
    NamespaceSelectionAgentConfig,
    RAGDelegationConfig,
)
from swiss_ai_hub.agent.agents.rag_agent import RAGAgent


def build() -> NamespaceSelectionAgentConfig:
    settings = AIHubSettings()
    return NamespaceSelectionAgentConfig(
        agent_id="shared-knowledge-selector",
        name=LocaleString(
            en="Shared Knowledge Selector",
            de="Geteiltes Wissen Auswahl",
            fr="Sélecteur Connaissances Partagées",
            it="Selettore Conoscenza Condivisa",
        ),
        description=LocaleString(
            en=(
                "Routes questions to the right namespace in the default and shared knowledge buckets, "
                "then delegates retrieval to the Shared Knowledge RAG agent."
            ),
            de=(
                "Leitet Fragen an den passenden Namespace im Standard- und geteilten Wissens-Bucket weiter "
                "und delegiert den Abruf an den Shared Knowledge RAG Agenten."
            ),
            fr=(
                "Achemine les questions vers le bon namespace dans les buckets par défaut et partagés, "
                "puis délègue la récupération à l'agent Shared Knowledge RAG."
            ),
            it=(
                "Indirizza le domande al namespace corretto nei bucket di conoscenza predefinito e condiviso, "
                "poi delega il recupero all'agente Shared Knowledge RAG."
            ),
        ),
        icon="mage:book",
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.0, timeout=60.0),
        ),
        bucket_names=[
            settings.DEFAULT_BUCKET_NAME,
            settings.SHARED_BUCKET_NAME,
        ],
        rag_delegation=RAGDelegationConfig(
            rag_agent=AgentRef(
                agent_class=RAGAgent.__name__,
                agent_id="shared-knowledge-rag",
            ),
        ),
        max_conversation_history_entries=20,
    )
