"""Form definition for RAGAgent configuration."""

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS, Checkbox, Group, InputNumber
from aihub_lib.nats.events.form.components import (
    create_agent_identity_form,
    create_few_shot_guard_examples_form,
    create_insight_retriever_config_form,
    create_knowledge_retriever_config_form,
    create_llm_config_form,
    create_reranking_config_form,
)
from aihub_lib.nats.events.form.helpers import create_locale_string_group


def create_rag_agent_config_form() -> list[ALL_FORM_OPTIONS]:
    """
    Creates the complete form definition for RAGAgentConfig.
    """
    form: list[ALL_FORM_OPTIONS] = []

    # =============================================================================
    # Agent Identity
    # =============================================================================
    form.extend(create_agent_identity_form())

    # =============================================================================
    # LLM Configuration
    # =============================================================================
    form.append(create_llm_config_form())

    # =============================================================================
    # Context & Retrieval Settings
    # =============================================================================
    form.append(
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
        )
    )
    form.append(
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
        )
    )
    form.append(
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
        )
    )

    # =============================================================================
    # Reranking Configuration
    # =============================================================================
    form.append(create_reranking_config_form())

    # =============================================================================
    # Retrievers Configuration
    # =============================================================================
    form.append(
        Group(
            name="retrievers",
            label=LocaleString(
                en="Retrievers",
                de="Retriever",
                fr="Récupérateurs",
                it="Recuperatori",
            ),
            children=[
                create_knowledge_retriever_config_form(name="0"),
                create_insight_retriever_config_form(name="1"),
            ],
        )
    )

    # =============================================================================
    # Few-Shot Guard Examples
    # =============================================================================
    form.append(create_few_shot_guard_examples_form())

    # =============================================================================
    # Prompts
    # =============================================================================
    form.append(
        create_locale_string_group(
            name="system_prompt",
            label=LocaleString(
                en="System Prompt",
                de="Systemprompt",
                fr="Prompt système",
                it="Prompt di sistema",
            ),
            input_type="textarea",
            rows=10,
            help_text=LocaleString(
                en="The system prompt that guides the agent's behavior and responses.",
                de="Der Systemprompt, der das Verhalten und die Antworten des Agenten steuert.",
                fr="Le prompt système qui guide le comportement et les réponses de l'agent.",
                it="Il prompt di sistema che guida il comportamento e le risposte dell'agente.",
            ),
        )
    )
    form.append(
        create_locale_string_group(
            name="context_prompt",
            label=LocaleString(
                en="Context Prompt",
                de="Kontextprompt",
                fr="Prompt de contexte",
                it="Prompt di contesto",
            ),
            input_type="textarea",
            rows=5,
            help_text=LocaleString(
                en="Prompt template for providing context (e.g., retrieved documents) to the LLM.",
                de="Prompt-Vorlage für die Bereitstellung von Kontext (z.B. abgerufene Dokumente) an das LLM.",
                fr="Modèle de prompt pour fournir le contexte (par ex. documents récupérés) au LLM.",
                it="Template del prompt per fornire contesto (es. documenti recuperati) all'LLM.",
            ),
        )
    )
    form.append(
        create_locale_string_group(
            name="context_insufficient_prompt",
            label=LocaleString(
                en="Context Insufficient Prompt",
                de="Unzureichender-Kontext-Prompt",
                fr="Prompt contexte insuffisant",
                it="Prompt contesto insufficiente",
            ),
            input_type="textarea",
            rows=3,
            help_text=LocaleString(
                en="Prompt used when the retrieved context is insufficient to answer the user's question.",
                de="Prompt, der verwendet wird, wenn der abgerufene Kontext nicht ausreicht.",
                fr="Prompt utilisé lorsque le contexte récupéré est insuffisant pour répondre.",
                it="Prompt utilizzato quando il contesto recuperato è insufficiente per rispondere.",
            ),
        )
    )

    return form
