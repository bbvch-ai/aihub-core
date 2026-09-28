from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import Checkbox, LocaleInput
from swiss_ai_hub.core.generative_ai import FewShotGuardExample, KnowledgeRetrieverConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.capabilities.memory.memory_enabled_agent_config import MemoryEnabledAgentConfig
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)


class RAGAgentConfig(MemoryEnabledAgentConfig):
    """
    Configuration for a RAGAgent with multiple retrieval sources.

    The conversational and memory fields come from the capability config bases; what is declared here is
    retrieval: sources, reranking, the guards and the prompts that frame retrieved context.

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
    condense_question: Annotated[
        bool | Checkbox,
        Field(description="Retrieval embeds one standalone question, so RAG condenses by default."),
    ] = True
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

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RAGAgentConfig."""
        base = AgentConfig.as_form()

        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            **cls.conversational_form_elements(),
            **cls.memory_form_elements(),
            retrievers=[KnowledgeRetrieverConfig.as_form()],
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
        )
