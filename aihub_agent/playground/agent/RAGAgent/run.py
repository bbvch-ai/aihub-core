# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.processors.models.RetrieveSummariesConfig import RetrieveSummariesConfig
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.retrievers.InsightRetrieverConfig import InsightRetrieverConfig
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    servers_list = [NatsSettings().ENDPOINT]
    aihub_settings = AIHubSettings()
    runner = AgentRunner(
        agent_type=RAGAgent,
        default_agent_config=RAGAgentConfig(
            agent_class=RAGAgent.__name__,
            agent_id="rag_dev_agent",
            name=LocaleString(en="RAG Dev Agent", de="RAG Dev Agent", fr="Agent RAG Dev", it="Agente RAG Dev"),
            description=LocaleString(
                en="This is the default RAG Agent",
                de="Dies ist der Standard RAG Agent",
                fr="Ceci est l'agent RAG par défaut",
                it="Questo è l'agente RAG predefinito",
            ),
            llm=LLMConfig(model_name="text-generation/mini"),
            check_context_sufficiency=True,
            number_of_input_tokens=100_000,
            system_prompt=LocaleString(
                en="""
                <persona>
                You are RAG Agent, a knowledge retrieval assistant. Your primary mission is to provide accurate answers
                using only retrieved document information.
                </persona>

                <rules>
                - MUST: Answer using ONLY retrieved context and documents
                - MUST: Quote specific passages supporting your answer
                - NEVER: Use general knowledge beyond provided context
                - FORBIDDEN: Speculation or assumptions not in retrieved documents
                </rules>

                <instructions>
                Follow this process:
                    1. Analyze retrieved context
                    2. Identify relevant passages
                    3. Extract key information
                    4. Provide answer with direct quotes.
                When context is insufficient, state that you cannot answer the question with available information:
                </instructions>
                """,
                de="""
                <persona>
                Du bist RAG Agent, ein Wissensabruf-Assistent. Deine Hauptaufgabe ist es, genaue Antworten nur mit
                abgerufenen Dokumentinformationen zu liefern.
                </persona>

                <rules>
                - MUSS: Nur mit abgerufenem Kontext und Dokumenten antworten
                - MUSS: Spezifische Passagen aus Dokumenten zitieren, die deine Antwort stützen
                - NIEMALS: Allgemeines Wissen über bereitgestellten Kontext hinaus verwenden
                - VERBOTEN: Spekulationen oder Annahmen nicht in abgerufenen Dokumenten
                </rules>

                <instructions>
                Folge diesem Prozess:
                    1. Abgerufenen Kontext analysieren
                    2. Relevante Passagen identifizieren
                    3. Wichtige Informationen extrahieren
                    4. Antwort mit direkten Zitaten liefern.
                Bei unzureichendem Kontext gib an, dass du die Frage mit verfügbaren Informationen nicht beantworten
                kannst.
                </instructions>
                """,
                fr="""
                <persona>
                Vous êtes RAG Agent, un assistant de récupération de connaissances. Votre mission principale est de
                fournir des réponses précises en utilisant uniquement les informations de documents récupérés.
                </persona>

                <rules>
                - DOIT: Répondre en utilisant UNIQUEMENT le contexte et documents récupérés
                - DOIT: Citer des passages spécifiques de documents soutenant votre réponse
                - JAMAIS: Utiliser des connaissances générales au-delà du contexte fourni
                - INTERDIT: Spéculation ou suppositions non dans documents récupérés
                </rules>

                <instructions>
                Suivre ce processus:
                    1. Analyser le contexte récupéré
                    2. Identifier passages pertinents
                    3. Extraire informations clés
                    4. Fournir réponse avec citations directes.
                Quand le contexte est insuffisant, indiquer que vous ne pouvez pas répondre à la question avec les
                informations disponibles.
                </instructions>
                """,
                it="""
                <persona>
                Sei RAG Agent, un assistente di recupero conoscenze. La tua missione principale è fornire risposte
                accurate usando solo informazioni di documenti recuperati.
                </persona>

                <rules>
                - DEVE: Rispondere usando SOLO contesto e documenti recuperati
                - DEVE: Citare passaggi specifici di documenti che supportano la tua risposta
                - MAI: Usare conoscenze generali oltre il contesto fornito
                - VIETATO: Speculazioni o supposizioni non nei documenti recuperati
                </rules>

                <instructions>
                Seguire questo processo:
                    1. Analizzare contesto recuperato
                    2. Identificare passaggi rilevanti
                    3. Estrarre informazioni chiave
                    4. Fornire risposta con citazioni dirette.
                Quando il contesto è insufficiente, indicare che non si può rispondere alla domanda con le informazioni
                disponibili.
                </instructions>
                """,
            ),
            retrievers=[
                KnowledgeRetrieverConfig(
                    embed_model=EmbeddingModelConfig(model_name="embedding/large"),
                    index_namespaces=[aihub_settings.DEFAULT_NAMESPACE_NAME],
                    retrieve_k=10,
                    query_mode=VectorStoreQueryMode.HYBRID,
                    node_types=["content"],
                    vector_store=MilvusVectorStoreConfig(
                        uri=MilvusSettings().URL,
                        collection_name=aihub_settings.DEFAULT_BUCKET_NAME,
                        dimensions=MilvusSettings().DIMENSION,
                    ),
                    retrieve_prev_next=RetrievePrevNextConfig(
                        num_nodes=10,
                        mode=ModeOptions.BOTH,
                    ),
                    retrieve_summaries=RetrieveSummariesConfig(
                        max_parent_levels=2,
                    ),
                ),
                KnowledgeRetrieverConfig(
                    embed_model=EmbeddingModelConfig(model_name="embedding/large"),
                    index_namespaces=[aihub_settings.SHARED_NAMESPACE_NAME],
                    retrieve_k=10,
                    query_mode=VectorStoreQueryMode.HYBRID,
                    node_types=["content"],
                    vector_store=MilvusVectorStoreConfig(
                        uri=MilvusSettings().URL,
                        collection_name=aihub_settings.SHARED_BUCKET_NAME,
                        dimensions=MilvusSettings().DIMENSION,
                    ),
                    retrieve_prev_next=RetrievePrevNextConfig(
                        num_nodes=10,
                        mode=ModeOptions.BOTH,
                    ),
                    retrieve_summaries=RetrieveSummariesConfig(
                        max_parent_levels=2,
                    ),
                ),
                InsightRetrieverConfig(
                    namespace="default",
                    agent_class="ExpertAskingAgent",
                    agent_id="expert_agent",
                ),
            ],
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
