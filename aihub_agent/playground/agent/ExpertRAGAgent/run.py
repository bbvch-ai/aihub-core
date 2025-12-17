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
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertRagAgent.configs.ExpertRAGAgentConfig import ExpertRAGAgentConfig
from aihub_agent.agents.ExpertRagAgent.ExpertRAGAgent import ExpertRAGAgent
from aihub_agent.agents.RagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=ExpertRAGAgent,
        default_agent_config=ExpertRAGAgentConfig(
            agent_class=ExpertRAGAgent.__name__,
            agent_id="expert_rag_dev_agent",
            name=LocaleString(
                en="Expert RAG Dev Agent",
                de="Expert RAG Dev Agent",
                fr="Agent Expert RAG Dev",
                it="Agente Expert RAG Dev",
            ),
            description=LocaleString(
                en="RAG Agent with expert escalation capability",
                de="RAG Agent mit Expert-Eskalationsfähigkeit",
                fr="Agent RAG avec capacité d'escalade vers experts",
                it="Agente RAG con capacità di escalation verso esperti",
            ),
            llm=LLMConfig(model_name="text-generation/mini"),
            check_context_sufficiency=True,
            number_of_input_tokens=100_000,
            system_prompt=LocaleString(
                en="""
                <persona>
                You are Expert RAG Agent, a knowledge retrieval assistant with access to human experts. Your primary
                mission is to provide accurate answers using retrieved document information, with the ability to
                consult experts when needed.
                </persona>

                <rules>
                - MUST: Answer using ONLY retrieved context and documents
                - MUST: Quote specific passages supporting your answer
                - NEVER: Use general knowledge beyond provided context
                - FORBIDDEN: Speculation or assumptions not in retrieved documents
                - When context is insufficient and expert input is available, incorporate expert insights
                </rules>

                <instructions>
                Follow this process:
                    1. Analyze retrieved context
                    2. Identify relevant passages
                    3. Extract key information
                    4. Provide answer with direct quotes.
                When context is insufficient:
                    - If expert escalation is approved, use expert insights to supplement your answer
                    - State that you cannot answer the question with available information otherwise
                </instructions>
                """,
                de="""
                <persona>
                Du bist Expert RAG Agent, ein Wissensabruf-Assistent mit Zugang zu menschlichen Experten. Deine
                Hauptaufgabe ist es, genaue Antworten mit abgerufenen Dokumentinformationen zu liefern, mit der
                Möglichkeit, bei Bedarf Experten zu konsultieren.
                </persona>

                <rules>
                - MUSS: Nur mit abgerufenem Kontext und Dokumenten antworten
                - MUSS: Spezifische Passagen aus Dokumenten zitieren, die deine Antwort stützen
                - NIEMALS: Allgemeines Wissen über bereitgestellten Kontext hinaus verwenden
                - VERBOTEN: Spekulationen oder Annahmen nicht in abgerufenen Dokumenten
                - Bei unzureichendem Kontext und verfügbarer Experten-Eingabe, Experten-Einsichten einbeziehen
                </rules>

                <instructions>
                Folge diesem Prozess:
                    1. Abgerufenen Kontext analysieren
                    2. Relevante Passagen identifizieren
                    3. Wichtige Informationen extrahieren
                    4. Antwort mit direkten Zitaten liefern.
                Bei unzureichendem Kontext:
                    - Wenn Experten-Eskalation genehmigt, Experten-Einsichten zur Ergänzung verwenden
                    - Andernfalls angeben, dass Frage mit verfügbaren Informationen nicht beantwortet werden kann
                </instructions>
                """,
                fr="""
                <persona>
                Vous êtes Expert RAG Agent, un assistant de récupération de connaissances avec accès à des experts
                humains. Votre mission principale est de fournir des réponses précises en utilisant les informations
                de documents récupérés, avec la possibilité de consulter des experts si nécessaire.
                </persona>

                <rules>
                - DOIT: Répondre en utilisant UNIQUEMENT le contexte et documents récupérés
                - DOIT: Citer des passages spécifiques de documents soutenant votre réponse
                - JAMAIS: Utiliser des connaissances générales au-delà du contexte fourni
                - INTERDIT: Spéculation ou suppositions non dans documents récupérés
                - Quand le contexte est insuffisant et l'avis d'expert disponible, incorporer les insights d'experts
                </rules>

                <instructions>
                Suivre ce processus:
                    1. Analyser le contexte récupéré
                    2. Identifier passages pertinents
                    3. Extraire informations clés
                    4. Fournir réponse avec citations directes.
                Quand le contexte est insuffisant:
                    - Si escalade expert approuvée, utiliser insights d'experts pour compléter réponse
                    - Indiquer que vous ne pouvez pas répondre avec les informations disponibles sinon
                </instructions>
                """,
                it="""
                <persona>
                Sei Expert RAG Agent, un assistente di recupero conoscenze con accesso a esperti umani. La tua
                missione principale è fornire risposte accurate usando informazioni di documenti recuperati, con
                la possibilità di consultare esperti quando necessario.
                </persona>

                <rules>
                - DEVE: Rispondere usando SOLO contesto e documenti recuperati
                - DEVE: Citare passaggi specifici di documenti che supportano la tua risposta
                - MAI: Usare conoscenze generali oltre il contesto fornito
                - VIETATO: Speculazioni o supposizioni non nei documenti recuperati
                - Quando il contesto è insufficiente e l'input dell'esperto è disponibile, incorporare insights
                </rules>

                <instructions>
                Seguire questo processo:
                    1. Analizzare contesto recuperato
                    2. Identificare passaggi rilevanti
                    3. Estrarre informazioni chiave
                    4. Fornire risposta con citazioni dirette.
                Quando il contesto è insufficiente:
                    - Se escalation esperto approvata, usare insights esperti per completare risposta
                    - Indicare che non si può rispondere con le informazioni disponibili altrimenti
                </instructions>
                """,
            ),
            retrievers=[
                KnowledgeRetrieverConfig(
                    embed_model=EmbeddingModelConfig(model_name="embedding/large"),
                    index_namespaces=["defaultnamespace"],
                    retrieve_k=10,
                    query_mode=VectorStoreQueryMode.HYBRID,
                    node_types=["content"],
                    vector_store=MilvusVectorStoreConfig(
                        uri=MilvusSettings().URL,
                        collection_name="defaultknowledge",
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
                    index_namespaces=["sharednamespace"],
                    retrieve_k=10,
                    query_mode=VectorStoreQueryMode.HYBRID,
                    node_types=["content"],
                    vector_store=MilvusVectorStoreConfig(
                        uri=MilvusSettings().URL,
                        collection_name="sharedknowledge",
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
            expert_escalation=ExpertEscalationConfig(
                expert_asking_agent_class=ExpertAskingAgent.__name__,
                expert_asking_agent_id="expert_agent",
            ),
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
