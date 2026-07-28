from typing import Annotated, Self

from pydantic import Field, model_validator
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import InputNumber, LocaleInput
from swiss_ai_hub.core.generative_ai import (
    FewShotGuardExample,
    KnowledgeRetrieverConfig,
    LLMConfig,
    OrgMemoryReadConfig,
)
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)


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
    task_llm: Annotated[
        LLMConfig | None,
        Field(
            default=None,
            description=(
                "Task LLM used for auxiliary tasks like standalone-question condensation, context/few-shot "
                "guards, meta-question detection, LLM routing, and conversation title + follow-up question "
                "generation. Falls back to the main LLM when disabled."
            ),
            title="Task LLM",
        ),
    ] = None
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(description="Maximum tokens allowed in input to manage context size or cost."),
    ] = 128000
    context_sufficient_guard: Annotated[
        ContextSufficientGuardStepConfig,
        Field(
            description="Configuration for the context-sufficient guard step.",
            title="Context Sufficient Guard",
        ),
    ] = ContextSufficientGuardStepConfig()
    retrievers: Annotated[
        list[KnowledgeRetrieverConfig],
        Field(description="List of knowledge retriever configurations.", title="Retrievers"),
    ]
    reranking_config: Annotated[
        RerankingConfig | None,
        Field(description="Configuration for reranking retrieved documents to improve relevance.", title="Reranking"),
    ] = None
    few_shot_guard_examples: Annotated[
        list[FewShotGuardExample],
        Field(
            description="Examples for the few-shot guard to define which user requests are accepted.",
            title="Few-Shot Guard Examples",
        ),
    ] = []
    user_memory: Annotated[
        UserMemoryConfig,
        Field(description="Configuration for user-scoped memory.", title="User Memory"),
    ] = UserMemoryConfig()
    org_memory: Annotated[
        OrgMemoryReadConfig | None,
        Field(
            description="Scoping for the organization memory the agent may read. Disable to skip organization memory.",
            title="Organization Memory",
        ),
    ] = OrgMemoryReadConfig()

    @model_validator(mode="after")
    def default_task_llm_to_main_llm(self) -> Self:
        """Auxiliary steps read `task_llm` directly, so an unset or blank picker falls back to the main llm."""
        if self.task_llm is None or not self.task_llm.model_name:
            self.task_llm = self.llm
        return self

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RAGAgentConfig."""
        base = AgentConfig.as_form()

        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            llm=LLMConfig.as_form(),
            task_llm=LLMConfig.as_form(),
            retrievers=[KnowledgeRetrieverConfig.as_form()],
            number_of_input_tokens=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.number_of_input_tokens.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.number_of_input_tokens.help"),
                min=1024,
                max=128000,
                step=1024,
            ),
            context_sufficient_guard=ContextSufficientGuardStepConfig.as_form(),
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
            user_memory=UserMemoryConfig.as_form(),
            org_memory=OrgMemoryReadConfig.as_form(),
        )
