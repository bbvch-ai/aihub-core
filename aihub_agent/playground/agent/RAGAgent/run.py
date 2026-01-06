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
from aihub_lib.nats.events.form import (
    Checkbox,
    Group,
    InputNumber,
    InputText,
    MultiSelect,
    Repeater,
    Select,
    Slider,
    Textarea,
)
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    servers_list = [NatsSettings().ENDPOINT]
    aihub_settings = AIHubSettings()

    # Complete form definition covering all RAGAgentConfig options
    form = [
        # =============================================================================
        # Agent Identity Group
        # =============================================================================
        Group(
            name="name",
            label=LocaleString(
                en="Agent Name",
                de="Agent-Name",
                fr="Nom de l'agent",
                it="Nome dell'agente",
            ),
            children=[
                InputText(
                    name="en",
                    label=LocaleString(en="English", de="Englisch", fr="Anglais", it="Inglese"),
                    help=LocaleString(
                        en="Display name for the agent (English)",
                        de="Anzeigename des Agenten (Englisch)",
                        fr="Nom d'affichage de l'agent (Anglais)",
                        it="Nome visualizzato dell'agente (Inglese)",
                    ),
                ),
                InputText(
                    name="de",
                    label=LocaleString(en="German", de="Deutsch", fr="Allemand", it="Tedesco"),
                    help=LocaleString(
                        en="Display name for the agent (German)",
                        de="Anzeigename des Agenten (Deutsch)",
                        fr="Nom d'affichage de l'agent (Allemand)",
                        it="Nome visualizzato dell'agente (Tedesco)",
                    ),
                ),
                InputText(
                    name="fr",
                    label=LocaleString(en="French", de="Französisch", fr="Français", it="Francese"),
                    help=LocaleString(
                        en="Display name for the agent (French)",
                        de="Anzeigename des Agenten (Französisch)",
                        fr="Nom d'affichage de l'agent (Français)",
                        it="Nome visualizzato dell'agente (Francese)",
                    ),
                ),
                InputText(
                    name="it",
                    label=LocaleString(en="Italian", de="Italienisch", fr="Italien", it="Italiano"),
                    help=LocaleString(
                        en="Display name for the agent (Italian)",
                        de="Anzeigename des Agenten (Italienisch)",
                        fr="Nom d'affichage de l'agent (Italien)",
                        it="Nome visualizzato dell'agente (Italiano)",
                    ),
                ),
            ],
        ),
        Group(
            name="description",
            label=LocaleString(
                en="Agent Description",
                de="Agent-Beschreibung",
                fr="Description de l'agent",
                it="Descrizione dell'agente",
            ),
            children=[
                Textarea(
                    name="en",
                    label=LocaleString(en="English", de="Englisch", fr="Anglais", it="Inglese"),
                    help=LocaleString(
                        en="Description of the agent's purpose (English)",
                        de="Beschreibung des Agentenzwecks (Englisch)",
                        fr="Description de l'objectif de l'agent (Anglais)",
                        it="Descrizione dello scopo dell'agente (Inglese)",
                    ),
                    rows=3,
                    auto_resize=True,
                ),
                Textarea(
                    name="de",
                    label=LocaleString(en="German", de="Deutsch", fr="Allemand", it="Tedesco"),
                    help=LocaleString(
                        en="Description of the agent's purpose (German)",
                        de="Beschreibung des Agentenzwecks (Deutsch)",
                        fr="Description de l'objectif de l'agent (Allemand)",
                        it="Descrizione dello scopo dell'agente (Tedesco)",
                    ),
                    rows=3,
                    auto_resize=True,
                ),
                Textarea(
                    name="fr",
                    label=LocaleString(en="French", de="Französisch", fr="Français", it="Francese"),
                    help=LocaleString(
                        en="Description of the agent's purpose (French)",
                        de="Beschreibung des Agentenzwecks (Französisch)",
                        fr="Description de l'objectif de l'agent (Français)",
                        it="Descrizione dello scopo dell'agente (Francese)",
                    ),
                    rows=3,
                    auto_resize=True,
                ),
                Textarea(
                    name="it",
                    label=LocaleString(en="Italian", de="Italienisch", fr="Italien", it="Italiano"),
                    help=LocaleString(
                        en="Description of the agent's purpose (Italian)",
                        de="Beschreibung des Agentenzwecks (Italienisch)",
                        fr="Description de l'objectif de l'agent (Italien)",
                        it="Descrizione dello scopo dell'agente (Italiano)",
                    ),
                    rows=3,
                    auto_resize=True,
                ),
            ],
        ),
        InputText(
            name="icon",
            label=LocaleString(
                en="Icon",
                de="Symbol",
                fr="Icône",
                it="Icona",
            ),
            help=LocaleString(
                en="Icon identifier for the agent (e.g., 'meteor-icons:robot')",
                de="Symbol-Bezeichner für den Agenten (z.B. 'meteor-icons:robot')",
                fr="Identifiant d'icône pour l'agent (par ex. 'meteor-icons:robot')",
                it="Identificatore icona per l'agente (es. 'meteor-icons:robot')",
            ),
        ),
        InputText(
            name="agent_class",
            label=LocaleString(
                en="Agent Class",
                de="Agent-Klasse",
                fr="Classe de l'agent",
                it="Classe dell'agente",
            ),
            help=LocaleString(
                en="The class name of the agent (read-only)",
                de="Der Klassenname des Agenten (schreibgeschützt)",
                fr="Le nom de la classe de l'agent (lecture seule)",
                it="Il nome della classe dell'agente (sola lettura)",
            ),
            disabled=True,
        ),
        InputText(
            name="agent_id",
            label=LocaleString(
                en="Agent ID",
                de="Agent-ID",
                fr="ID de l'agent",
                it="ID dell'agente",
            ),
            help=LocaleString(
                en="The unique identifier of the agent (read-only)",
                de="Die eindeutige Kennung des Agenten (schreibgeschützt)",
                fr="L'identifiant unique de l'agent (lecture seule)",
                it="L'identificatore univoco dell'agente (sola lettura)",
            ),
            disabled=True,
        ),
        # =============================================================================
        # LLM Configuration Group (LLMConfig)
        # =============================================================================
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
                # LLMParameter nested config
                Group(
                    name="default_parameter",
                    label=LocaleString(
                        en="LLM Parameters",
                        de="LLM-Parameter",
                        fr="Paramètres LLM",
                        it="Parametri LLM",
                    ),
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
                                en="Controls randomness. Lower = more deterministic, higher = more creative.",
                                de="Steuert die Zufälligkeit. Niedriger = deterministischer, höher = kreativer.",
                                fr="Contrôle l'aléatoire. Bas = déterministe, haut = créatif.",
                                it="Controlla la casualità. Basso = deterministico, alto = creativo.",
                            ),
                            min=0.0,
                            max=2.0,
                            step=0.1,
                        ),
                        Checkbox(
                            name="logprobs",
                            label=LocaleString(
                                en="Return Log Probabilities",
                                de="Log-Wahrscheinlichkeiten zurückgeben",
                                fr="Retourner les probabilités logarithmiques",
                                it="Restituisci probabilità logaritmiche",
                            ),
                            help=LocaleString(
                                en="Whether to return log probabilities per token.",
                                de="Ob Log-Wahrscheinlichkeiten pro Token zurückgegeben werden.",
                                fr="Retourner ou non les probabilités logarithmiques par token.",
                                it="Se restituire le probabilità logaritmiche per token.",
                            ),
                            binary=True,
                        ),
                        InputNumber(
                            name="top_logprobs",
                            label=LocaleString(
                                en="Top Log Probabilities",
                                de="Top-Log-Wahrscheinlichkeiten",
                                fr="Top probabilités logarithmiques",
                                it="Top probabilità logaritmiche",
                            ),
                            help=LocaleString(
                                en="Number of top token log probabilities to return (0-20).",
                                de="Anzahl der Top-Token-Log-Wahrscheinlichkeiten (0-20).",
                                fr="Nombre de probabilités logarithmiques des tokens à retourner (0-20).",
                                it="Numero di probabilità logaritmiche dei token da restituire (0-20).",
                            ),
                            min=0,
                            max=20,
                            step=1,
                            show_buttons=True,
                        ),
                        InputNumber(
                            name="timeout",
                            label=LocaleString(
                                en="API Timeout (seconds)",
                                de="API-Timeout (Sekunden)",
                                fr="Délai d'attente API (secondes)",
                                it="Timeout API (secondi)",
                            ),
                            help=LocaleString(
                                en="Timeout in seconds for API requests. Default: 600.0",
                                de="Timeout in Sekunden für API-Anfragen. Standard: 600.0",
                                fr="Délai d'attente en secondes pour les requêtes API. Par défaut: 600.0",
                                it="Timeout in secondi per le richieste API. Default: 600.0",
                            ),
                            min=0,
                            max=3600,
                            step=10,
                            show_buttons=True,
                        ),
                    ],
                ),
            ],
        ),
        # =============================================================================
        # Context & Retrieval Settings (RAGAgentConfig top-level fields)
        # =============================================================================
        InputNumber(
            name="number_of_input_tokens",
            label=LocaleString(
                en="Max Input Tokens",
                de="Maximale Eingabe-Tokens",
                fr="Tokens d'entrée maximum",
                it="Token di input massimi",
            ),
            help=LocaleString(
                en="Maximum number of tokens allowed in input to manage context size or cost.",
                de="Maximale Anzahl der Tokens in der Eingabe zur Verwaltung der Kontextgröße oder Kosten.",
                fr="Nombre maximum de tokens autorisés en entrée pour gérer la taille du contexte ou les coûts.",
                it="Numero massimo di token consentiti in input per gestire la dimensione del contesto o i costi.",
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
                en="When enabled, the agent verifies if the retrieved context contains enough info.",
                de="Wenn aktiviert, prüft der Agent, ob der abgerufene Kontext genügend Infos enthält.",
                fr="L'agent vérifie si le contexte récupéré contient suffisamment d'informations.",
                it="L'agente verifica se il contesto recuperato contiene informazioni sufficienti.",
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
                en="Maximum number of retrieval attempts if context is insufficient (1-10). Default: 1",
                de="Maximale Anzahl der Abrufversuche, wenn der Kontext unzureichend ist (1-10). Standard: 1",
                fr="Nombre maximum de tentatives de récupération si le contexte est insuffisant (1-10). Par défaut: 1",
                it="Numero massimo di tentativi di recupero se il contesto è insufficiente (1-10). Default: 1",
            ),
            min=1,
            max=10,
            step=1,
            show_buttons=True,
        ),
        # =============================================================================
        # Reranking Configuration Group (RerankingConfig + RerankingModelConfig)
        # =============================================================================
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
                        de="Wenn aktiviert, werden Dokumente für bessere Relevanz neu geordnet.",
                        fr="Les documents récupérés seront reclassés pour une meilleure pertinence.",
                        it="I documenti recuperati verranno riordinati per una migliore rilevanza.",
                    ),
                    binary=True,
                ),
                # RerankingModelConfig nested config
                Group(
                    name="reranking_model",
                    label=LocaleString(
                        en="Reranking Model",
                        de="Reranking-Modell",
                        fr="Modèle de reclassement",
                        it="Modello di riordinamento",
                    ),
                    children=[
                        Select(
                            name="model_name",
                            label=LocaleString(
                                en="Reranking Model",
                                de="Reranking-Modell",
                                fr="Modèle de reclassement",
                                it="Modello di riordinamento",
                            ),
                            help=LocaleString(
                                en="The model to use for reranking documents.",
                                de="Das Modell für das Reranking von Dokumenten.",
                                fr="Le modèle à utiliser pour le reclassement des documents.",
                                it="Il modello da utilizzare per il riordinamento dei documenti.",
                            ),
                            options=[
                                {"label": "Rerank Model", "value": "reranking/default"},
                            ],
                            option_label="label",
                            option_value="value",
                        ),
                        InputNumber(
                            name="top_n",
                            label=LocaleString(
                                en="Top N Documents",
                                de="Top N Dokumente",
                                fr="Top N documents",
                                it="Top N documenti",
                            ),
                            help=LocaleString(
                                en="Number of top documents to keep after reranking (1-100).",
                                de="Anzahl der Top-Dokumente nach dem Reranking (1-100).",
                                fr="Nombre de documents à conserver après le reclassement (1-100).",
                                it="Numero di documenti da mantenere dopo il riordinamento (1-100).",
                            ),
                            min=1,
                            max=100,
                            step=1,
                            show_buttons=True,
                        ),
                    ],
                ),
            ],
        ),
        # =============================================================================
        # Retrievers Configuration (list[RetrieverConfig])
        # Supports KnowledgeRetrieverConfig and InsightRetrieverConfig
        # =============================================================================
        Group(
            name="retrievers",
            label=LocaleString(
                en="Retrievers",
                de="Retriever",
                fr="Récupérateurs",
                it="Recuperatori",
            ),
            children=[
                # Knowledge Retriever Configuration
                Group(
                    name="0",
                    label=LocaleString(
                        en="Knowledge Retriever",
                        de="Wissens-Retriever",
                        fr="Récupérateur de connaissances",
                        it="Recuperatore di conoscenza",
                    ),
                    children=[
                        Select(
                            name="retriever_type",
                            label=LocaleString(
                                en="Retriever Type",
                                de="Retriever-Typ",
                                fr="Type de récupérateur",
                                it="Tipo di recuperatore",
                            ),
                            help=LocaleString(
                                en="The type of retriever (knowledge or insight).",
                                de="Der Typ des Retrievers (Wissen oder Einsicht).",
                                fr="Le type de récupérateur (connaissance ou insight).",
                                it="Il tipo di recuperatore (conoscenza o insight).",
                            ),
                            options=[
                                {"label": "Knowledge", "value": "knowledge"},
                                {"label": "Insight", "value": "insight"},
                            ],
                            option_label="label",
                            option_value="value",
                        ),
                        Group(
                            name="embed_model",
                            label=LocaleString(
                                en="Embedding Model",
                                de="Einbettungsmodell",
                                fr="Modèle d'embedding",
                                it="Modello di embedding",
                            ),
                            children=[
                                Select(
                                    name="model_name",
                                    label=LocaleString(
                                        en="Model Name",
                                        de="Modellname",
                                        fr="Nom du modèle",
                                        it="Nome del modello",
                                    ),
                                    help=LocaleString(
                                        en="The embedding model to use for vector search.",
                                        de="Das Einbettungsmodell für die Vektorsuche.",
                                        fr="Le modèle d'embedding à utiliser pour la recherche vectorielle.",
                                        it="Il modello di embedding da utilizzare per la ricerca vettoriale.",
                                    ),
                                    options=[
                                        {"label": "Large Embedding Model", "value": "embedding/large"},
                                        {"label": "Small Embedding Model", "value": "embedding/small"},
                                    ],
                                    option_label="label",
                                    option_value="value",
                                ),
                            ],
                        ),
                        InputText(
                            name="index_namespaces",
                            label=LocaleString(
                                en="Index Namespaces",
                                de="Index-Namespaces",
                                fr="Espaces de noms d'index",
                                it="Namespace degli indici",
                            ),
                            help=LocaleString(
                                en="Comma-separated list of namespaces to retrieve from.",
                                de="Kommagetrennte Liste der Namespaces für den Abruf.",
                                fr="Liste de namespaces séparés par des virgules.",
                                it="Elenco di namespace separati da virgole.",
                            ),
                        ),
                        InputNumber(
                            name="retrieve_k",
                            label=LocaleString(
                                en="Documents to Retrieve",
                                de="Abzurufende Dokumente",
                                fr="Documents à récupérer",
                                it="Documenti da recuperare",
                            ),
                            help=LocaleString(
                                en="The number of documents to retrieve per query (1-100).",
                                de="Die Anzahl der Dokumente pro Abfrage (1-100).",
                                fr="Le nombre de documents à récupérer par requête (1-100).",
                                it="Il numero di documenti da recuperare per query (1-100).",
                            ),
                            min=1,
                            max=100,
                            step=1,
                            show_buttons=True,
                        ),
                        Select(
                            name="query_mode",
                            label=LocaleString(
                                en="Query Mode",
                                de="Abfragemodus",
                                fr="Mode de requête",
                                it="Modalità di query",
                            ),
                            help=LocaleString(
                                en="How the vector store should be queried.",
                                de="Wie der Vektorspeicher abgefragt werden soll.",
                                fr="Comment le magasin de vecteurs doit être interrogé.",
                                it="Come deve essere interrogato il vector store.",
                            ),
                            options=[
                                {"label": "Default", "value": "default"},
                                {"label": "Hybrid", "value": "hybrid"},
                                {"label": "Sparse", "value": "sparse"},
                            ],
                            option_label="label",
                            option_value="value",
                        ),
                        MultiSelect(
                            name="node_types",
                            label=LocaleString(
                                en="Node Types",
                                de="Knotentypen",
                                fr="Types de nœuds",
                                it="Tipi di nodo",
                            ),
                            help=LocaleString(
                                en="The types of nodes to retrieve (summary and/or content).",
                                de="Die Arten der abzurufenden Knoten (Zusammenfassung und/oder Inhalt).",
                                fr="Les types de nœuds à récupérer (résumé et/ou contenu).",
                                it="I tipi di nodi da recuperare (riepilogo e/o contenuto).",
                            ),
                            options=[
                                {"label": "Content", "value": "content"},
                                {"label": "Summary", "value": "summary"},
                            ],
                            option_label="label",
                            option_value="value",
                        ),
                    ],
                ),
                # Insight Retriever Configuration
                Group(
                    name="1",
                    label=LocaleString(
                        en="Insight Retriever",
                        de="Einsichts-Retriever",
                        fr="Récupérateur d'insights",
                        it="Recuperatore di insight",
                    ),
                    children=[
                        Select(
                            name="retriever_type",
                            label=LocaleString(
                                en="Retriever Type",
                                de="Retriever-Typ",
                                fr="Type de récupérateur",
                                it="Tipo di recuperatore",
                            ),
                            help=LocaleString(
                                en="The type of retriever (knowledge or insight).",
                                de="Der Typ des Retrievers (Wissen oder Einsicht).",
                                fr="Le type de récupérateur (connaissance ou insight).",
                                it="Il tipo di recuperatore (conoscenza o insight).",
                            ),
                            options=[
                                {"label": "Knowledge", "value": "knowledge"},
                                {"label": "Insight", "value": "insight"},
                            ],
                            option_label="label",
                            option_value="value",
                        ),
                        InputText(
                            name="namespace",
                            label=LocaleString(
                                en="Namespace",
                                de="Namespace",
                                fr="Espace de noms",
                                it="Namespace",
                            ),
                            help=LocaleString(
                                en="The namespace to filter insights by.",
                                de="Der Namespace zum Filtern von Einsichten.",
                                fr="L'espace de noms pour filtrer les insights.",
                                it="Il namespace per filtrare gli insight.",
                            ),
                        ),
                        InputText(
                            name="agent_class",
                            label=LocaleString(
                                en="Agent Class",
                                de="Agent-Klasse",
                                fr="Classe d'agent",
                                it="Classe agente",
                            ),
                            help=LocaleString(
                                en="The agent class to filter insights by.",
                                de="Die Agent-Klasse zum Filtern von Einsichten.",
                                fr="La classe d'agent pour filtrer les insights.",
                                it="La classe dell'agente per filtrare gli insight.",
                            ),
                        ),
                        InputText(
                            name="agent_id",
                            label=LocaleString(
                                en="Agent ID",
                                de="Agent-ID",
                                fr="ID de l'agent",
                                it="ID agente",
                            ),
                            help=LocaleString(
                                en="The agent ID to filter insights by.",
                                de="Die Agent-ID zum Filtern von Einsichten.",
                                fr="L'ID de l'agent pour filtrer les insights.",
                                it="L'ID dell'agente per filtrare gli insight.",
                            ),
                        ),
                    ],
                ),
            ],
        ),
        # =============================================================================
        # Few-Shot Guard Examples (list[FewShotGuardExample])
        # Examples for the few-shot guard to define which user requests are accepted
        # Dynamic repeater allowing add/remove of examples
        # =============================================================================
        Repeater(
            name="few_shot_guard_examples",
            label=LocaleString(
                en="Few-Shot Guard Examples",
                de="Few-Shot-Guard-Beispiele",
                fr="Exemples de garde few-shot",
                it="Esempi di guardia few-shot",
            ),
            add_label=LocaleString(
                en="Add Example",
                de="Beispiel hinzufügen",
                fr="Ajouter un exemple",
                it="Aggiungi esempio",
            ),
            children=[
                Group(
                    name="user",
                    label=LocaleString(
                        en="User Message",
                        de="Benutzernachricht",
                        fr="Message utilisateur",
                        it="Messaggio utente",
                    ),
                    children=[
                        InputText(
                            name="en",
                            label=LocaleString(en="English", de="Englisch", fr="Anglais", it="Inglese"),
                        ),
                        InputText(
                            name="de",
                            label=LocaleString(en="German", de="Deutsch", fr="Allemand", it="Tedesco"),
                        ),
                        InputText(
                            name="fr",
                            label=LocaleString(en="French", de="Französisch", fr="Français", it="Francese"),
                        ),
                        InputText(
                            name="it",
                            label=LocaleString(en="Italian", de="Italienisch", fr="Italien", it="Italiano"),
                        ),
                    ],
                ),
                Checkbox(
                    name="success",
                    label=LocaleString(
                        en="Should Accept",
                        de="Sollte akzeptieren",
                        fr="Devrait accepter",
                        it="Dovrebbe accettare",
                    ),
                    help=LocaleString(
                        en="Whether this type of request should be accepted (true) or rejected (false).",
                        de="Ob diese Art von Anfrage akzeptiert (wahr) oder abgelehnt (falsch) werden soll.",
                        fr="Si ce type de demande doit être accepté (vrai) ou rejeté (faux).",
                        it="Se questo tipo di richiesta deve essere accettata (vero) o rifiutata (falso).",
                    ),
                    binary=True,
                ),
                Group(
                    name="reason",
                    label=LocaleString(
                        en="Reason",
                        de="Begründung",
                        fr="Raison",
                        it="Motivo",
                    ),
                    children=[
                        InputText(
                            name="en",
                            label=LocaleString(en="English", de="Englisch", fr="Anglais", it="Inglese"),
                        ),
                        InputText(
                            name="de",
                            label=LocaleString(en="German", de="Deutsch", fr="Allemand", it="Tedesco"),
                        ),
                        InputText(
                            name="fr",
                            label=LocaleString(en="French", de="Französisch", fr="Français", it="Francese"),
                        ),
                        InputText(
                            name="it",
                            label=LocaleString(en="Italian", de="Italienisch", fr="Italien", it="Italiano"),
                        ),
                    ],
                ),
            ],
        ),
        # =============================================================================
        # System Prompt Group (LocaleString)
        # =============================================================================
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
                        en="The system prompt that guides the agent's behavior and responses (English).",
                        de="Der Systemprompt, der das Verhalten und die Antworten des Agenten steuert (Englisch).",
                        fr="Le prompt système qui guide le comportement et les réponses de l'agent (Anglais).",
                        it="Il prompt di sistema che guida il comportamento e le risposte dell'agente (Inglese).",
                    ),
                    rows=10,
                    auto_resize=True,
                ),
                Textarea(
                    name="de",
                    label=LocaleString(
                        en="German",
                        de="Deutsch",
                        fr="Allemand",
                        it="Tedesco",
                    ),
                    help=LocaleString(
                        en="The system prompt that guides the agent's behavior and responses (German).",
                        de="Der Systemprompt, der das Verhalten und die Antworten des Agenten steuert (Deutsch).",
                        fr="Le prompt système qui guide le comportement et les réponses de l'agent (Allemand).",
                        it="Il prompt di sistema che guida il comportamento e le risposte dell'agente (Tedesco).",
                    ),
                    rows=10,
                    auto_resize=True,
                ),
                Textarea(
                    name="fr",
                    label=LocaleString(
                        en="French",
                        de="Französisch",
                        fr="Français",
                        it="Francese",
                    ),
                    help=LocaleString(
                        en="The system prompt that guides the agent's behavior and responses (French).",
                        de="Der Systemprompt, der das Verhalten und die Antworten des Agenten steuert (Französisch).",
                        fr="Le prompt système qui guide le comportement et les réponses de l'agent (Français).",
                        it="Il prompt di sistema che guida il comportamento e le risposte dell'agente (Francese).",
                    ),
                    rows=10,
                    auto_resize=True,
                ),
                Textarea(
                    name="it",
                    label=LocaleString(
                        en="Italian",
                        de="Italienisch",
                        fr="Italien",
                        it="Italiano",
                    ),
                    help=LocaleString(
                        en="The system prompt that guides the agent's behavior and responses (Italian).",
                        de="Der Systemprompt, der das Verhalten und die Antworten des Agenten steuert (Italienisch).",
                        fr="Le prompt système qui guide le comportement et les réponses de l'agent (Italien).",
                        it="Il prompt di sistema che guida il comportamento e le risposte dell'agente (Italiano).",
                    ),
                    rows=10,
                    auto_resize=True,
                ),
            ],
        ),
        # =============================================================================
        # Context Prompt Group (LocaleString) - Optional template for context
        # =============================================================================
        Group(
            name="context_prompt",
            label=LocaleString(
                en="Context Prompt",
                de="Kontextprompt",
                fr="Prompt de contexte",
                it="Prompt di contesto",
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
                        en="Prompt template for providing context (e.g., retrieved documents) to the LLM.",
                        de="Prompt-Vorlage für die Bereitstellung von Kontext (z.B. abgerufene Dokumente) an das LLM.",
                        fr="Modèle de prompt pour fournir le contexte (par ex. documents récupérés) au LLM.",
                        it="Template del prompt per fornire contesto (es. documenti recuperati) all'LLM.",
                    ),
                    rows=5,
                    auto_resize=True,
                ),
                Textarea(
                    name="de",
                    label=LocaleString(
                        en="German",
                        de="Deutsch",
                        fr="Allemand",
                        it="Tedesco",
                    ),
                    help=LocaleString(
                        en="Context prompt template (German).",
                        de="Kontextprompt-Vorlage (Deutsch).",
                        fr="Modèle de prompt de contexte (Allemand).",
                        it="Template del prompt di contesto (Tedesco).",
                    ),
                    rows=5,
                    auto_resize=True,
                ),
                Textarea(
                    name="fr",
                    label=LocaleString(
                        en="French",
                        de="Französisch",
                        fr="Français",
                        it="Francese",
                    ),
                    help=LocaleString(
                        en="Context prompt template (French).",
                        de="Kontextprompt-Vorlage (Französisch).",
                        fr="Modèle de prompt de contexte (Français).",
                        it="Template del prompt di contesto (Francese).",
                    ),
                    rows=5,
                    auto_resize=True,
                ),
                Textarea(
                    name="it",
                    label=LocaleString(
                        en="Italian",
                        de="Italienisch",
                        fr="Italien",
                        it="Italiano",
                    ),
                    help=LocaleString(
                        en="Context prompt template (Italian).",
                        de="Kontextprompt-Vorlage (Italienisch).",
                        fr="Modèle de prompt de contexte (Italien).",
                        it="Template del prompt di contesto (Italiano).",
                    ),
                    rows=5,
                    auto_resize=True,
                ),
            ],
        ),
        # =============================================================================
        # Context Insufficient Prompt Group (LocaleString)
        # =============================================================================
        Group(
            name="context_insufficient_prompt",
            label=LocaleString(
                en="Context Insufficient Prompt",
                de="Unzureichender-Kontext-Prompt",
                fr="Prompt contexte insuffisant",
                it="Prompt contesto insufficiente",
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
                        en="Prompt used when the retrieved context is insufficient to answer the user's question.",
                        de="Prompt, der verwendet wird, wenn der abgerufene Kontext nicht ausreicht.",
                        fr="Prompt utilisé lorsque le contexte récupéré est insuffisant pour répondre.",
                        it="Prompt utilizzato quando il contesto recuperato è insufficiente per rispondere.",
                    ),
                    rows=3,
                    auto_resize=True,
                ),
                Textarea(
                    name="de",
                    label=LocaleString(
                        en="German",
                        de="Deutsch",
                        fr="Allemand",
                        it="Tedesco",
                    ),
                    help=LocaleString(
                        en="Context insufficient prompt (German).",
                        de="Unzureichender-Kontext-Prompt (Deutsch).",
                        fr="Prompt contexte insuffisant (Allemand).",
                        it="Prompt contesto insufficiente (Tedesco).",
                    ),
                    rows=3,
                    auto_resize=True,
                ),
                Textarea(
                    name="fr",
                    label=LocaleString(
                        en="French",
                        de="Französisch",
                        fr="Français",
                        it="Francese",
                    ),
                    help=LocaleString(
                        en="Context insufficient prompt (French).",
                        de="Unzureichender-Kontext-Prompt (Französisch).",
                        fr="Prompt contexte insuffisant (Français).",
                        it="Prompt contesto insufficiente (Francese).",
                    ),
                    rows=3,
                    auto_resize=True,
                ),
                Textarea(
                    name="it",
                    label=LocaleString(
                        en="Italian",
                        de="Italienisch",
                        fr="Italien",
                        it="Italiano",
                    ),
                    help=LocaleString(
                        en="Context insufficient prompt (Italian).",
                        de="Unzureichender-Kontext-Prompt (Italienisch).",
                        fr="Prompt contexte insuffisant (Italien).",
                        it="Prompt contesto insufficiente (Italiano).",
                    ),
                    rows=3,
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
        form=form,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
