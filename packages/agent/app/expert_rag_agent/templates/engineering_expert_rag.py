from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.generative_ai import (
    EmbeddingModelConfig,
    KnowledgeRetrieverConfig,
    LLMConfig,
    LLMParameter,
    OrgMemoryReadConfig,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig

from swiss_ai_hub.agent.agents.expert_rag_agent import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.expert_escalation_config import ExpertEscalationConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)


def build() -> ExpertRAGAgentConfig:
    settings = AIHubSettings()
    return ExpertRAGAgentConfig(
        agent_id="engineering-expert-rag",
        name=LocaleString(
            en="Engineering Expert RAG",
            de="Engineering Experten-RAG",
            fr="RAG Expert en ingénierie",
            it="RAG Esperto di ingegneria",
        ),
        description=LocaleString(
            en=(
                "Answers engineering questions from the shared knowledge base and escalates to a human"
                " engineering expert when retrieved context is insufficient."
            ),
            de=(
                "Beantwortet technische Fragen aus der geteilten Wissensbasis und eskaliert an einen menschlichen"
                " Experten, wenn der Kontext nicht ausreicht."
            ),
            fr=(
                "Répond aux questions techniques depuis la base de connaissances partagée et escalade vers un"
                " expert humain lorsque le contexte récupéré est insuffisant."
            ),
            it=(
                "Risponde a domande tecniche dalla base di conoscenza condivisa e inoltra a un esperto umano"
                " quando il contesto recuperato non è sufficiente."
            ),
        ),
        icon="mage:book-open-check",
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.0, timeout=120.0),
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
        org_memory=OrgMemoryReadConfig(
            default_tenant_namespace="engineering",
            allowed_tenant_namespaces=["engineering", "shared"],
            rerank_organization_memory=True,
        ),
        expert_escalation=ExpertEscalationConfig(
            agent=AgentRef(
                agent_class="ExpertAskingAgent",
                agent_id="engineering-expert",
            ),
        ),
    )
