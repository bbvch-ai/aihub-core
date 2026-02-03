from typing import Annotated, Self

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.memory.MemorySettings import MemorySettings
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.constraints import Ge
from aihub_lib.nats.events.form.elements.Checkbox import Checkbox
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.nats.events.form.elements.InputText import InputText
from aihub_lib.nats.events.form.elements.LocaleInput import LocaleInput
from pydantic import Field

from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from aihub_agent.i18n.AgentLocaleString import AgentLocaleString


class RAGAgentConfig(AgentConfig):
    """
    Configuration for a RAGAgent with multiple retrieval sources.

    Supports:
    - Multiple retrievers (knowledge base)
    - Organization memory (expert knowledge shared across users)
    - User memory (personalized context for individual users)

    Note: For expert escalation functionality, use ExpertRAGAgentConfig instead.

    Supports duality pattern for form rendering and data validation.
    """

    system_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="System prompt to guide the agent's behavior and responses.", title="System Prompt"),
    ] = AgentLocaleString.from_i18n_path("agent.rag_agent.config.system_prompt.default")
    context_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(
            description="Prompt template for providing context (e.g., retrieved documents) to the LLM.",
            title="Context Prompt",
        ),
    ] = AgentLocaleString.from_i18n_path("agent.rag_agent.config.context_prompt.default")
    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(description="Maximum tokens allowed in input to manage context size or cost."),
    ] = 128000
    max_hops: Annotated[
        int | InputNumber,
        Field(
            description="Maximum number of retrieval hops to perform if context is insufficient.",
        ),
        Ge(1),
    ] = 1
    check_context_sufficiency: Annotated[
        bool | None | Checkbox,
        Field(
            description="Whether or not to check if the retrieved context is sufficient for generating a response.",
        ),
    ] = False
    context_insufficient_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(
            description="Prompt used when the retrieved context is insufficient to answer the user's question.",
            title="Context Insufficient Prompt",
        ),
    ] = AgentLocaleString.from_i18n_path("agent.rag_agent.config.context_insufficient_prompt.default")
    retrievers: Annotated[
        list[KnowledgeRetrieverConfig],
        Field(description="List of knowledge retriever configurations.", title="Retrievers"),
    ]
    reranking_config: Annotated[
        RerankingConfig,
        Field(description="Configuration for reranking retrieved documents to improve relevance.", title="Reranking"),
    ] = RerankingConfig()
    few_shot_guard_examples: Annotated[
        list[FewShotGuardExample],
        Field(
            description="Examples for the few-shot guard to define which user requests are accepted.",
            title="Few-Shot Guard Examples",
        ),
    ] = []

    # Organization memory configuration
    enable_organization_memory: Annotated[
        bool | Checkbox,
        Field(description="Whether to retrieve organization memories (expert knowledge) for context."),
    ] = True
    tenant_id: Annotated[
        str,
        Field(description="Tenant ID for organization memory scoping."),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_ID)
    tenant_namespace: Annotated[
        str | InputText | None,
        Field(description="Tenant namespace for department-level memory isolation. Uses default if None."),
    ] = None

    # User memory configuration
    enable_user_memory_retrieval: Annotated[
        bool | Checkbox,
        Field(description="Whether to retrieve user-specific memories for personalized context."),
    ] = True
    enable_user_memory_storage: Annotated[
        bool | Checkbox,
        Field(description="Whether to store new memories from conversations for future retrieval."),
    ] = True

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RAGAgentConfig."""
        base = AgentConfig.as_form()

        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            agent_class=base.agent_class,
            llm=LLMConfig.as_form(),
            retrievers=[KnowledgeRetrieverConfig.as_form()],
            number_of_input_tokens=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.number_of_input_tokens.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.number_of_input_tokens.help"),
                min=1024,
                max=128000,
                step=1024,
            ),
            check_context_sufficiency=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.check_context_sufficiency.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.check_context_sufficiency.help"),
                ref="check_context_sufficiency_enabled",
            ),
            max_hops=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.max_hops.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.max_hops.help"),
                min=1,
                max=10,
                step=1,
            ),
            reranking_config=RerankingConfig.as_form(),
            few_shot_guard_examples=[FewShotGuardExample.as_form()],
            system_prompt=LocaleString.as_form(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.system_prompt.label"),
                help_text=AgentLocaleString.from_i18n_path("agent.rag_agent.config.system_prompt.help"),
                input_type="textarea",
            ),
            context_prompt=LocaleString.as_form(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.context_prompt.label"),
                help_text=AgentLocaleString.from_i18n_path("agent.rag_agent.config.context_prompt.help"),
                input_type="textarea",
            ),
            context_insufficient_prompt=LocaleString.as_form(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.context_insufficient_prompt.label"),
                help_text=AgentLocaleString.from_i18n_path("agent.rag_agent.config.context_insufficient_prompt.help"),
                input_type="textarea",
                condition_if="$get(check_context_sufficiency_enabled).value",
            ),
            enable_organization_memory=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_organization_memory.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_organization_memory.help"),
                ref="check_organization_memory_enabled",
            ),
            tenant_namespace=InputText(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.tenant_namespace.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.tenant_namespace.help"),
                condition_if="$get(check_organization_memory_enabled).value",
            ),
            enable_user_memory_retrieval=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_user_memory_retrieval.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_user_memory_retrieval.help"),
            ),
            enable_user_memory_storage=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_user_memory_storage.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.enable_user_memory_storage.help"),
            ),
        )
