from swiss_ai_hub.core.generative_ai import (
    EmbeddingModelConfig,
    KnowledgeRetrieverConfig,
    LLMConfig,
    LLMParameter,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig

from swiss_ai_hub.agent.agents.rag_agent import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)


def build() -> RAGAgentConfig:
    settings = AIHubSettings()
    return RAGAgentConfig(
        agent_id="shared-knowledge-rag",
        name=LocaleString(
            en="Shared Knowledge RAG",
            de="Geteiltes Wissen RAG",
            fr="RAG Connaissances Partagées",
            it="RAG Conoscenza Condivisa",
        ),
        description=LocaleString(
            en=(
                "Answers questions by retrieving from the default and shared knowledge buckets. "
                "Pairs with the Shared Knowledge Selector namespace routing agent."
            ),
            de=(
                "Beantwortet Fragen durch Abruf aus dem Standard- und geteilten Wissens-Bucket. "
                "Ergänzt den Shared Knowledge Selector für die Namespace-Auswahl."
            ),
            fr=(
                "Répond aux questions en interrogeant les buckets de connaissances par défaut et partagés. "
                "Complète l'agent Shared Knowledge Selector pour le routage de namespace."
            ),
            it=(
                "Risponde alle domande recuperando dai bucket di conoscenza predefinito e condiviso. "
                "Si abbina all'agente Shared Knowledge Selector per il routing dei namespace."
            ),
        ),
        icon="mage:book-open",
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.1, timeout=120.0),
        ),
        number_of_input_tokens=128000,
        context_sufficient_guard=ContextSufficientGuardStepConfig(
            check_context_sufficiency=True,
            max_hops=2,
        ),
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=EmbeddingModelConfig(model_name="embedding/bge-m3"),
                vector_store=MilvusVectorStoreConfig(
                    collection_name=settings.DEFAULT_BUCKET_NAME,
                    index_namespaces=[settings.DEFAULT_NAMESPACE_NAME],
                ),
                retrieve_k=5,
                node_types=["content"],
            ),
            KnowledgeRetrieverConfig(
                embed_model=EmbeddingModelConfig(model_name="embedding/bge-m3"),
                vector_store=MilvusVectorStoreConfig(
                    collection_name=settings.SHARED_BUCKET_NAME,
                    index_namespaces=[settings.SHARED_NAMESPACE_NAME],
                ),
                retrieve_k=5,
                node_types=["content"],
            ),
        ],
        user_memory=UserMemoryConfig(
            enable_user_memory_retrieval=True,
            enable_user_memory_storage=True,
        ),
    )
