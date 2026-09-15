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
        # Deliberately self-contained: the Shared Knowledge Selector this once named is not part of the
        # standard blueprint set, so most tenants never see it and pointing an admin at it would dead-end.
        description=LocaleString(
            en=(
                "Answers questions from your knowledge bases, checks whether what it retrieved is enough "
                "to answer, and cites the documents it used."
            ),
            de=(
                "Beantwortet Fragen aus Ihren Wissensdatenbanken, prüft, ob das Abgerufene zur Antwort "
                "ausreicht, und nennt die verwendeten Dokumente."
            ),
            fr=(
                "Répond aux questions à partir de vos bases de connaissances, vérifie si les informations "
                "récupérées suffisent et cite les documents utilisés."
            ),
            it=(
                "Risponde alle domande dalle vostre basi di conoscenza, verifica se quanto recuperato è "
                "sufficiente e cita i documenti utilizzati."
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
