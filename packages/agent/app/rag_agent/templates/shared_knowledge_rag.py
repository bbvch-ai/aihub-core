from swiss_ai_hub.core.generative_ai import (
    EmbeddingModelConfig,
    FewShotGuardExample,
    KnowledgeRetrieverConfig,
    LLMConfig,
    LLMParameter,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig

from swiss_ai_hub.agent.agents.rag_agent import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step import ContextSufficientGuardStepConfig

_settings = AIHubSettings()

TEMPLATE = RAGAgentConfig(
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
        model_name="text-generation/gpt-oss-120b",
        default_parameter=LLMParameter(temperature=0.1, timeout=120.0),
    ),
    number_of_input_tokens=128000,
    context_sufficient_guard=ContextSufficientGuardStepConfig(
        check_context_sufficiency=True,
        max_hops=2,
        max_non_system_messages_in_guard=6,
    ),
    retrievers=[
        KnowledgeRetrieverConfig(
            embed_model=EmbeddingModelConfig(model_name="embedding/bge-m3"),
            vector_store=MilvusVectorStoreConfig(
                collection_name=_settings.DEFAULT_BUCKET_NAME,
                index_namespaces=[_settings.DEFAULT_NAMESPACE_NAME],
            ),
            retrieve_k=5,
            node_types=["content"],
        ),
        KnowledgeRetrieverConfig(
            embed_model=EmbeddingModelConfig(model_name="embedding/bge-m3"),
            vector_store=MilvusVectorStoreConfig(
                collection_name=_settings.SHARED_BUCKET_NAME,
                index_namespaces=[_settings.SHARED_NAMESPACE_NAME],
            ),
            retrieve_k=5,
            node_types=["content"],
        ),
    ],
    reranking_config=RerankingConfig(enabled=False),
    few_shot_guard_examples=[
        FewShotGuardExample(
            user=LocaleString(
                en="What is our company's vacation policy?",
                de="Wie lautet unsere Urlaubsregelung?",
                fr="Quelle est notre politique de vacances?",
                it="Qual è la nostra politica sulle ferie?",
            ),
            success=True,
            reason=LocaleString(
                en="Question concerns shared organizational knowledge retrievable from documents.",
                de="Frage betrifft geteiltes Unternehmenswissen, das aus Dokumenten abgerufen werden kann.",
                fr="La question porte sur des connaissances organisationnelles partagées, récupérables dans les documents.",
                it="La domanda riguarda conoscenze organizzative condivise, recuperabili dai documenti.",
            ),
        ),
        FewShotGuardExample(
            user=LocaleString(
                en="Book me a flight to Paris next Monday.",
                de="Buche mir einen Flug nach Paris nächsten Montag.",
                fr="Réserve-moi un vol pour Paris lundi prochain.",
                it="Prenotami un volo per Parigi lunedì prossimo.",
            ),
            success=False,
            reason=LocaleString(
                en="Request asks for an action (booking) outside the scope of knowledge retrieval.",
                de="Anfrage verlangt eine Aktion (Buchung), die ausserhalb des Wissensabruf-Umfangs liegt.",
                fr="La demande sollicite une action (réservation) hors du périmètre de récupération de connaissances.",
                it="La richiesta chiede un'azione (prenotazione) al di fuori dell'ambito del recupero di conoscenze.",
            ),
        ),
    ],
    enable_organization_memory=True,
    enable_user_memory_retrieval=True,
    enable_user_memory_storage=True,
)
