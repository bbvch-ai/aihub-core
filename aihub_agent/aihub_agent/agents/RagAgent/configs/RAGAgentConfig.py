from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.memory.MemorySettings import MemorySettings
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig


class RAGAgentConfig(AgentConfig):
    """
    Configuration for a RAGAgent with multiple retrieval sources.

    Supports:
    - Multiple retrievers (knowledge base)
    - Organization memory (expert knowledge shared across users)
    - User memory (personalized context for individual users)

    Note: For expert escalation functionality, use ExpertRAGAgentConfig instead.
    """

    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]

    retrievers: Annotated[
        list[KnowledgeRetrieverConfig],
        Field(description="List of knowledge retriever configurations."),
    ]

    number_of_input_tokens: Annotated[
        int, Field(description="Maximum tokens allowed in input to manage context size or cost.")
    ]
    context_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for providing context (e.g., retrieved documents) to the LLM."),
    ] = None
    few_shot_guard_examples: Annotated[
        list[FewShotGuardExample],
        Field(description="Examples for the few-shot guard to define which user requests are accepted."),
    ] = []
    check_context_sufficiency: Annotated[
        bool | None,
        Field(
            description="Whether or not to check if the retrieved context is sufficient for generating a response.",
        ),
    ] = False
    max_hops: Annotated[
        int,
        Field(
            description="Maximum number of retrieval hops to perform if context is insufficient.",
            ge=1,
        ),
    ] = 1
    system_prompt: Annotated[
        LocaleString | None,
        Field(description="System prompt to guide the agent's behavior and responses."),
    ] = None
    context_insufficient_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt used when the retrieved context is insufficient to answer the user's question."),
    ] = LocaleString(
        en=("Inform the user that you can not answer the question due to the following reason:"),
        de=("Informiere den Benutzer, dass du die Frage nicht beantworten kannst, aufgrund des folgenden Grundes:"),
        fr=("Informez l'utilisateur que vous ne pouvez pas répondre à la question pour la raison suivante :"),
        it=("Informa l'utente che non puoi rispondere alla domanda per il seguente motivo:"),
    )
    reranking_config: Annotated[
        RerankingConfig,
        Field(description="Configuration for reranking retrieved documents to improve relevance."),
    ] = RerankingConfig()

    # Organization memory configuration
    enable_organization_memory: Annotated[
        bool,
        Field(description="Whether to retrieve organization memories (expert knowledge) for context."),
    ] = True
    tenant_id: Annotated[
        str,
        Field(description="Tenant ID for organization memory scoping."),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_ID)
    tenant_namespace: Annotated[
        str | None,
        Field(description="Tenant namespace for department-level memory isolation. Uses default if None."),
    ] = None

    # User memory configuration
    enable_user_memory_retrieval: Annotated[
        bool,
        Field(description="Whether to retrieve user-specific memories for personalized context."),
    ] = True
    enable_user_memory_storage: Annotated[
        bool,
        Field(description="Whether to store new memories from conversations for future retrieval."),
    ] = True
