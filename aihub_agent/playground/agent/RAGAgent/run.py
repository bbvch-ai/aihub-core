import asyncio

from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.agents.RagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.RagAgent.configs.RetrieveSummariesConfig import RetrieveSummariesConfig
from aihub_agent.runners.AgentRunner import AgentRunner
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.retrievers import (
    InsightRetrieverConfig,
    KnowledgeRetrieverConfig,
    RetrieveSummariesConfig,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from aihub_lib.nats.events.form import Checkbox, Group, InputNumber, Select, Slider, Textarea
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.RagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    servers_list = [NatsSettings().ENDPOINT]

    # Define form elements explicitly using Groups for nested configuration
    # TODO create full default config
    form = [
        # LLM Configuration Group
        Group(
            name="llm",
            label=LocaleString(
                en="LLM Configuration",
                de="LLM-Konfiguration",
                fr="Configuration LLM",
                it="Configurazione LLM",
            ),
            children=[
                Select(
                    name="model_name",
                    label=LocaleString(
                        en="Model",
                        de="Modell",
                        fr="Modèle",
                        it="Modello",
                    ),
                    help=LocaleString(
                        en="The language model to use for generating responses.",
                        de="Das Sprachmodell für die Generierung von Antworten.",
                        fr="Le modèle de langage à utiliser pour générer des réponses.",
                        it="Il modello di linguaggio da utilizzare per generare risposte.",
                    ),
                    options=[
                        {"label": "Nano (Local, Fast)", "value": "text-generation/nano"},
                        {"label": "Mini (Local, Balanced)", "value": "text-generation/mini"},
                        {"label": "Large (Azure, Best Quality)", "value": "text-generation/large"},
                        {"label": "OCR (Azure, Vision)", "value": "text-generation/ocr"},
                    ],
                    option_label="label",
                    option_value="value",
                ),
                Group(
                    name="default_parameter",
                    children=[
                        Slider(
                            name="temperature",
                            label=LocaleString(
                                en="Temperature",
                                de="Temperatur",
                                fr="Température",
                                it="Temperatura",
                            ),
                            help=LocaleString(
                                en="Controls randomness in responses. Lower = more deterministic, higher = more creative.",
                                de="Steuert die Zufälligkeit der Antworten. Niedriger = deterministischer, höher = kreativer.",
                                fr="Contrôle l'aléatoire des réponses. Bas = déterministe, haut = créatif.",
                                it="Controlla la casualità nelle risposte. Basso = deterministico, alto = creativo.",
                            ),
                            min=0.0,
                            max=2.0,
                            step=0.1,
                        ),
                    ],
                ),
            ],
        ),
        # Retrieval Configuration Group
        Group(
            name="retrieve_step_config",
            label=LocaleString(
                en="Retrieval Configuration",
                de="Abruf-Konfiguration",
                fr="Configuration de récupération",
                it="Configurazione recupero",
            ),
            children=[
                InputNumber(
                    name="retrieve_k",
                    label=LocaleString(
                        en="Retrieve K Documents",
                        de="K Dokumente abrufen",
                        fr="Récupérer K documents",
                        it="Recupera K documenti",
                    ),
                    help=LocaleString(
                        en="Number of documents to retrieve from the vector store.",
                        de="Anzahl der Dokumente, die aus dem Vektorspeicher abgerufen werden.",
                        fr="Nombre de documents à récupérer du magasin de vecteurs.",
                        it="Numero di documenti da recuperare dal vector store.",
                    ),
                    min=1,
                    max=100,
                    step=1,
                    show_buttons=True,
                ),
            ],
        ),
        # Context Settings (top-level fields)
        InputNumber(
            name="number_of_input_tokens",
            label=LocaleString(
                en="Max Input Tokens",
                de="Maximale Eingabe-Tokens",
                fr="Tokens d'entrée maximum",
                it="Token di input massimi",
            ),
            help=LocaleString(
                en="Maximum number of tokens allowed in input to manage context size.",
                de="Maximale Anzahl der Tokens in der Eingabe zur Verwaltung der Kontextgröße.",
                fr="Nombre maximum de tokens autorisés en entrée pour gérer la taille du contexte.",
                it="Numero massimo di token consentiti in input per gestire la dimensione del contesto.",
            ),
            min=1024,
            max=128000,
            step=1024,
            show_buttons=True,
        ),
        Checkbox(
            name="check_context_sufficiency",
            label=LocaleString(
                en="Check Context Sufficiency",
                de="Kontext-Suffizienz prüfen",
                fr="Vérifier la suffisance du contexte",
                it="Verifica sufficienza contesto",
            ),
            help=LocaleString(
                en="When enabled, the agent will verify if the retrieved context contains enough information.",
                de="Wenn aktiviert, prüft der Agent, ob der abgerufene Kontext genügend Informationen enthält.",
                fr="Lorsqu'activé, l'agent vérifie si le contexte récupéré contient suffisamment d'informations.",
                it="Se abilitato, l'agente verifica se il contesto recuperato contiene informazioni sufficienti.",
            ),
            binary=True,
        ),
        InputNumber(
            name="max_hops",
            label=LocaleString(
                en="Max Retrieval Hops",
                de="Maximale Abruf-Sprünge",
                fr="Sauts de récupération maximum",
                it="Salti di recupero massimi",
            ),
            help=LocaleString(
                en="Maximum number of additional retrieval attempts if context is insufficient.",
                de="Maximale Anzahl zusätzlicher Abrufversuche, wenn der Kontext unzureichend ist.",
                fr="Nombre maximum de tentatives de récupération supplémentaires si le contexte est insuffisant.",
                it="Numero massimo di tentativi di recupero aggiuntivi se il contesto è insufficiente.",
            ),
            min=1,
            max=10,
            step=1,
            show_buttons=True,
        ),
        # Reranking Configuration Group
        Group(
            name="reranking_config",
            label=LocaleString(
                en="Reranking Configuration",
                de="Reranking-Konfiguration",
                fr="Configuration du reclassement",
                it="Configurazione riordinamento",
            ),
            children=[
                Checkbox(
                    name="enabled",
                    label=LocaleString(
                        en="Enable Reranking",
                        de="Reranking aktivieren",
                        fr="Activer le reclassement",
                        it="Abilita riordinamento",
                    ),
                    help=LocaleString(
                        en="When enabled, retrieved documents will be reranked for improved relevance.",
                        de="Wenn aktiviert, werden abgerufene Dokumente für bessere Relevanz neu geordnet.",
                        fr="Lorsqu'activé, les documents récupérés seront reclassés pour une meilleure pertinence.",
                        it="Se abilitato, i documenti recuperati verranno riordinati per una migliore rilevanza.",
                    ),
                    binary=True,
                ),
                Group(
                    name="reranking_model",
                    children=[
                        InputNumber(
                            name="top_n",
                            label=LocaleString(
                                en="Reranking Top N",
                                de="Reranking Top N",
                                fr="Top N du reclassement",
                                it="Top N riordinamento",
                            ),
                            help=LocaleString(
                                en="Number of top documents to keep after reranking.",
                                de="Anzahl der Top-Dokumente, die nach dem Reranking behalten werden.",
                                fr="Nombre de documents principaux à conserver après le reclassement.",
                                it="Numero di documenti principali da mantenere dopo il riordinamento.",
                            ),
                            min=1,
                            max=50,
                            step=1,
                            show_buttons=True,
                        ),
                    ],
                ),
            ],
        ),
        # System Prompt Group
        Group(
            name="system_prompt",
            label=LocaleString(
                en="System Prompt",
                de="Systemprompt",
                fr="Prompt système",
                it="Prompt di sistema",
            ),
            children=[
                Textarea(
                    name="en",
                    label=LocaleString(
                        en="English",
                        de="Englisch",
                        fr="Anglais",
                        it="Inglese",
                    ),
                    help=LocaleString(
                        en="The system prompt that guides the agent's behavior and responses.",
                        de="Der Systemprompt, der das Verhalten und die Antworten des Agenten steuert.",
                        fr="Le prompt système qui guide le comportement et les réponses de l'agent.",
                        it="Il prompt di sistema che guida il comportamento e le risposte dell'agente.",
                    ),
                    rows=10,
                    auto_resize=True,
                ),
            ],
        ),
    ]

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
        form=form,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
